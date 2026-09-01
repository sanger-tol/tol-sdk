# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging
import signal
from collections.abc import Callable
from typing import Any

from pika.adapters.blocking_connection import BlockingChannel

from pydantic import ValidationError

from tol.rabbitmq.config import RabbitmqConfig
from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.schema import MessageEnvelope

LOGGER = logging.getLogger(__name__)

Handler = Callable[[MessageEnvelope], None]


class MessageConsumer:
    """
    Generic consumer: validates each message as a `MessageEnvelope`,
    dispatches to the handler registered for `envelope.type`, then acks.
    Any failure nacks with requeue=False (message lands in the DLQ).
    """

    def __init__(
        self,
        connection: RabbitmqConnection,
        queue: str,
        handlers: dict[str, Handler]
    ) -> None:
        self.__connection = connection
        self.__queue = queue
        self.__handlers = handlers
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

    def __on_message(self, ch, method, properties, body) -> None:
        """Validate envelope, dispatches by type, ack. Nack failures."""
        try:
            envelope = MessageEnvelope.model_validate_json(body)
        except ValidationError:
            LOGGER.error('Invalid message envelope, nacking')
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        handler = self.__handlers.get(envelope.type)
        if handler is None:
            LOGGER.error('no handler for type %s, nacking', envelope.type)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        try:
            handler(envelope)
        except Exception:  # noqa BLE001
            LOGGER.exception(
                'Handler failed for %s, nacking.', envelope.id
            )
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        ch.basic_ack(delivery_tag=method.delivery_tag)


# Example entrypoint - apps copy this pattern, swapping in their own
# handlers and queue.
if __name__ == '__main__':
    """Run the notification consumer."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s'
    )

    from tol.rabbitmq.handlers import notification_handler
    from tol.rabbitmq.schema import NotificationChannel

    config = RabbitmqConfig.from_env()
    connection = RabbitmqConnection(config)

    # Log only until real senders are implemented - fine for testing
    dispatchers = {
        NotificationChannel.EMAIL: lambda d: LOGGER.info('EMAIL: %s', d),
        NotificationChannel.SLACK: lambda d: LOGGER.info('SLACK: %s', d),
    }

    consumer = MessageConsumer(
        connection,
        config.queue,
        {
            'notification': notification_handler(dispatchers)
        }
    )
    consumer.start()
