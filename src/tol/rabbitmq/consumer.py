# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging
import signal
from collections.abc import Callable
from typing import Any

from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from pydantic import ValidationError

from tol.rabbitmq.config import RabbitmqConfig
from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.schema import (NotificationChannel, NotificationDelivery,
                                 NotificationRequest, create_deliveries)

LOGGER = logging.getLogger(__name__)

Dispatcher = Callable[[NotificationDelivery], None]


class NotificationConsumer:
    """
    Central consumer: reads `NotificationRequest` messages from the queue,
    fans out to `NotificationDelivery` per channel/recipient, and dispatches
    to the injected channel senders.
    """

    def __init__(
        self,
        connection: RabbitmqConnection,
        queue: str,
        dispatchers: dict[NotificationChannel, Dispatcher]
    ) -> None:
        self.__connection = connection
        self.__queue = queue
        self.__dispatchers = dispatchers
        self.__channel: BlockingChannel | None = None

    def start(self) -> None:
        """
        Connect, declare quality of service, and block in the consume loop.
        """
        self.__install_signal_handlers()
        self.__connection.connect()
        self.__channel = self.__connection.channel
        self.__channel.basic_qos(prefetch_count=1)
        self.__channel.basic_consume(
            queue=self.__queue,
            on_message_callback=self.__on_message,
        )
        LOGGER.info('Consuming from queue %s', self.__queue)
        self.__channel.start_consuming()

    def stop(self) -> None:
        """Stop consuming and close the connection."""
        if self.__channel and self.__channel.is_open:
            self.__channel.stop_consuming()
        self.__connection.close()

    def process_one(self) -> None:
        """
        Consume exactly one message then return.

        Public seam for integration tests: call this instead of `start()`
        so the test can assert on the result without a blocking loop.
        """
        self.__connection.connect()
        self.__channel = self.__connection.channel
        self.__channel.basic_qos(prefetch_count=1)
        self.__channel.basic_consume(
            queue=self.__queue,
            on_message_callback=self.__on_message,
        )

        # Process one message then stop
        self.__channel.connection.process_data_events(time_limit=5)
        self.stop()

    def __on_message(
        self,
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        """Validate, fan out, dispatch, then ack. Nack on any failure."""
        try:
            request = NotificationRequest.model_validate_json(body)
        except ValidationError:
            LOGGER.error('Invalid notification payload, nacking.')
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        deliveries = create_deliveries(request)
        try:
            for delivery in deliveries:
                dispatcher = self.__dispatchers.get(delivery.channel)
                if dispatcher is None:
                    LOGGER.warning(
                        'No dispatcher for channel %s, skipping.',
                        delivery.channel
                    )
                    continue
                dispatcher(delivery)
        except Exception:  # noqa: BLE001
            LOGGER.exception('Dispatcher failed, nacking.')
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __install_signal_handlers(self) -> None:
        """
        Install signal handlers to gracefully
        stop consuming on SIGINT/SIGTERM.
        """

        def handler(signum: int, frame: Any) -> None:
            """Handle SIGINT/SIGTERM by stopping the consumer."""
            LOGGER.info('received signal %d, shutting down', signum)
            self.stop()

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)


if __name__ == '__main__':
    """Run the notification consumer."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s'
    )

    config = RabbitmqConfig.from_env()
    connection = RabbitmqConnection(config)

    # Log only until real senders are implemented - fine for testing
    dispatchers: dict[NotificationChannel, Dispatcher] = {
        NotificationChannel.EMAIL: lambda d: LOGGER.info('EMAIL: %s', d),
        NotificationChannel.SLACK: lambda d: LOGGER.info('SLACK: %s', d),
    }

    consumer = NotificationConsumer(connection, config.queue, dispatchers)
    consumer.start()
