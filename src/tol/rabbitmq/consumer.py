# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging
import signal
from collections.abc import Callable
from typing import Any

from pika.adapters.blocking_connection import BlockingChannel

from pydantic import ValidationError

from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.schema import MessageEnvelope

LOGGER = logging.getLogger(__name__)

Handler = Callable[[MessageEnvelope], None]


class MessageConsumer:
    """
    Generic consumer: validates each message as a `MessageEnvelope`,
    dispatches to the handler registered for `envelope.type`, then acks.
    Any failure nacks with requeue=False (message lands in the DLQ).

    No in-process reconnect: on connection loss `start()` raises and the
    process should exit - a restarting supervisor should take it from there.
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
        self.__received = False

    def start(self) -> None:
        """
        Consume until `stop()` (SIGINT/SIGTERM) or connection loss,
        then close the connection.
        """
        self.__install_signal_handlers()
        channel = self.__subscribe()
        LOGGER.info('Consuming from queue %s', self.__queue)
        try:
            channel.start_consuming()
        finally:
            self.__connection.close()

    def stop(self) -> None:
        """
        As the consume loop to exit once in-flight message is acked.
        Safe to call from a signal handler.
        """
        channel = self.__channel
        if channel is not None and channel.is_open:
            channel.connection.add_callback_threadsafe(channel.stop_consuming)

    def process_one(self, time_limit: float = 5) -> bool:
        """
        Wait up to `time_limit` seconds for one message, handle it, close.

        Returns True if a message was delivered. Test seam: use instead of
        `start()` to assert on the result without a blocking loop.
        """
        self.__received = False
        channel = self.__subscribe()
        try:
            channel.connection.process_data_events(time_limit=time_limit)
        finally:
            self.__connection.close()
        return self.__received

    def __subscribe(self) -> BlockingChannel:
        """Connect, set prefetch to 1 and register the message callback."""
        self.__connection.connect()
        channel = self.__connection.channel
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=self.__queue,
            on_message_callback=self.__on_message
        )
        self.__channel = channel
        return channel

    def __install_signal_handlers(self) -> None:
        """Stop gracefully on SIGINT/SIGTERM"""

        def handler(signum: int, frame: Any) -> None:
            """Request a stop; the in-flight message still completes."""
            LOGGER.info(
                'Received signal %d, stopping after in-flight message',
                signum
            )
            self.stop()

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

    def __on_message(self, ch, method, properties, body) -> None:
        """Validate envelope, dispatch by type, ack. Nack on failure."""
        self.__received = True

        try:
            envelope = MessageEnvelope.model_validate_json(body)
        except ValidationError:
            LOGGER.error('Invalid message envelope, nacking')
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        handler = self.__handlers.get(envelope.type)
        if handler is None:
            LOGGER.error('No handler for type %s, nacking', envelope.type)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        try:
            handler(envelope)
        except Exception:  # noqa BLE001
            LOGGER.exception('Handler failed for %s, nacking', envelope.id)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        ch.basic_ack(delivery_tag=method.delivery_tag)
