# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
import logging
import ssl

import pika
import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

from tol.rabbitmq.config import RabbitmqConfig

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class QueueSpec:
    """Declares one queue, its bindings and its dead-letter queue"""
    name: str
    binding_keys: tuple[str, ...]
    dead_letter: bool = True


def declare_topology(
    channel: BlockingChannel,
    exchange: str,
    specs: list[QueueSpec],
    dlx: str | None = None,
) -> None:
    """Declare the topic exchange plus each QueueSpec's queue/bindings/DLQ."""
    channel.exchange_declare(
        exchange=exchange,
        exchange_type='topic',
        durable=True
    )

    if dlx is not None:
        channel.exchange_declare(
            exchange=dlx,
            exchange_type='topic',
            durable=True
        )

    for spec in specs:
        arguments = None
        if spec.dead_letter and dlx is not None:
            arguments = {
                'x-dead-letter-exchange': dlx,
                'x-dead-letter-routing-key': f'dead.{spec.name}'
            }
        channel.queue_declare(
            queue=spec.name,
            durable=True,
            arguments=arguments
        )

        for key in spec.binding_keys:
            channel.queue_bind(
                queue=spec.name,
                exchange=exchange,
                routing_key=key
            )

        if spec.dead_letter and dlx is not None:
            dead_queue = f'{spec.name}.dead'
            channel.queue_declare(queue=dead_queue, durable=True)
            channel.queue_bind(
                queue=dead_queue,
                exchange=dlx,
                routing_key=f'dead.{spec.name}'
            )


class RabbitmqConnection:
    """
    Thin wrapper around pika BlockingConnection.

    Declares the exchange/queue/binding shape on connect.
    User as a context manager, or call connect()/close() manually.
    """

    __slots__ = ('__config', '__connection', '__channel')

    def __init__(
        self,
        config: RabbitmqConfig
    ) -> None:

        self.__config = config
        self.__connection: pika.BlockingConnection | None = None
        self.__channel: BlockingChannel | None = None

    def __enter__(self) -> 'RabbitmqConnection':
        """Connect to RabbitMQ and return self."""
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        """Close the connection to RabbitMQ."""
        self.close()

    @property
    def channel(self) -> BlockingChannel:
        """The raw pika channel. Raises if not connected."""
        if self.__channel is None:
            raise pika.exceptions.ConnectionClosedByBroker(0, 'Not connected')
        return self.__channel

    def connect(self) -> None:
        """Connect to RabbitMQ and declare the exchange/queue/binding."""
        LOGGER.info(
            'Connecting to RabbitMQ at %s:%s vhost %s', self.__config.host,
            self.__config.port, self.__config.vhost)
        self.__connection = pika.BlockingConnection(self.__build_parameters())
        self.__channel = self.__connection.channel()
        self.__declare_topology()

    def close(self) -> None:
        """Close the connection to RabbitMQ, if open."""
        if self.__connection is not None and self.__connection.is_open:
            LOGGER.info('Closing RabbitMQ connection')
            self.__connection.close()
        self.__connection = None
        self.__channel = None

    def __build_parameters(self) -> pika.ConnectionParameters:
        """Build the pika ConnectionParameters from the RabbitmqConfig."""
        ssl_options = None
        if self.__config.use_ssl:
            ssl_options = pika.SSLOptions(
                ssl.create_default_context(), self.__config.host)
        return pika.ConnectionParameters(
            host=self.__config.host,
            port=self.__config.port,
            virtual_host=self.__config.vhost,
            credentials=pika.PlainCredentials(
                username=self.__config.username,
                password=self.__config.password),
            ssl_options=ssl_options
        )

    def __declare_topology(self) -> None:
        """
        Declare the exchange, queue, and binding for the notification system.
        """
        spec = QueueSpec(
            name=self.__config.queue,
            binding_keys=(self.__config.routing_key,),
            dead_letter=True
        )

        declare_topology(
            self.channel,
            self.__config.exchange,
            [spec],
            dlx=self.__config.dlx
        )
