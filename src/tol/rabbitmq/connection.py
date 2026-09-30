# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging
import ssl
from dataclasses import dataclass

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
    dead_max_length: int = 10_000
    delivery_limit: int = 5

    def __post_init__(self) -> None:
        # ('key') is a str, not a tuple, it would bind one chartacter at a time
        if isinstance(self.binding_keys, str):
            raise TypeError(
                f'QueueSpec {self.name!r}: binding_keys must be a tuple, '
                f'got str {self.binding_keys!r} (missing trailing comma?)'
            )


def declare_topology(
    channel: BlockingChannel,
    exchange: str,
    specs: list[QueueSpec],
    dlx: str | None = None,
    declare_exchanges: bool = True
) -> None:
    """
    Declare the exchanges plus each QueueSpec's quorum queue, bindings
    and dead-letter queue.

    With `declare_exchanges=False` the exchanges should already exist and
    will not cause errors on config mismatch.
    The system will fail fast if this is not the case.
    """
    for name in (exchange, dlx):
        if name is None:
            continue
        if declare_exchanges:
            channel.exchange_declare(
                exchange=name,
                exchange_type='topic',
                durable=True
            )
        else:
            channel.exchange_declare(exchange=name, passive=True)

    for spec in specs:
        arguments: dict[str, object] = {
            'x-queue-type': 'quorum',
            'x-delivery-limit': spec.delivery_limit
        }

        if spec.dead_letter and dlx is not None:
            arguments |= {
                'x-dead-letter-exchange': dlx,
                'x-dead-letter-routing-key': f'dead.{spec.name}',
                'x-dead-letter-strategy': 'at-least-once',
                'x-overflow': 'reject-publish',
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
            channel.queue_declare(
                queue=dead_queue,
                durable=True,
                arguments={
                    'x-queue-type': 'quorum',
                    'x-max-length': spec.dead_max_length
                }
            )
            channel.queue_bind(
                queue=dead_queue,
                exchange=dlx,
                routing_key=f'dead.{spec.name}'
            )


class RabbitmqConnection:
    """
    Thin wrapper around pika BlockingConnection.

    Declares the exchange/queue/binding shape on connect.
    Use as a context manager, or call connect()/close() manually.
    """

    __slots__ = ('__config', '__specs', '__connection', '__channel')

    def __init__(
        self,
        config: RabbitmqConfig,
        specs: list[QueueSpec] | None = None
    ) -> None:

        self.__config = config
        self.__specs = specs if specs is not None else []
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
            raise RuntimeError('RabbitmqConnection is not connected')
        return self.__channel

    def connect(self) -> None:
        """
        Connect (or reopen a dead channel) and declare the topology.
        No-op when the connection and channel are both open.
        """
        if self.__is_open():
            LOGGER.debug('Already connected to RabbitMQ; skipping connect')
            return

        if self.__connection is not None and self.__connection.is_open:
            LOGGER.warning('RabbitMQ channel closed; reopening')
        else:
            LOGGER.info(
                'Connecting to RabbitMQ at %s:%s vhost %s', self.__config.host,
                self.__config.port, self.__config.vhost
            )

            self.__connection = pika.BlockingConnection(self.__build_parameters())

        self.__channel = self.__connection.channel()
        self.__declare_topology()

    def __is_open(self) -> bool:
        """Returns true when both the connection and channel are usable."""
        return (
            self.__connection is not None
            and self.__connection.is_open
            and self.__channel is not None
            and self.__channel.is_open
        )

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
            context = ssl.create_default_context(cafile=self.__config.ca_file)
            ssl_options = pika.SSLOptions(context, self.__config.host)
        return pika.ConnectionParameters(
            host=self.__config.host,
            port=self.__config.port,
            virtual_host=self.__config.vhost,
            credentials=pika.PlainCredentials(
                username=self.__config.username,
                password=self.__config.password),
            ssl_options=ssl_options,
            heartbeat=self.__config.heartbeat,
            blocked_connection_timeout=(
                self.__config.blocked_connection_timeout
            ),
            socket_timeout=self.__config.socket_timeout,
            connection_attempts=self.__config.connection_attempts,
            retry_delay=self.__config.retry_delay
        )

    def __declare_topology(self) -> None:
        """
        Declare the parameters, and binding for the notification system.
        """
        declare_topology(
            self.channel,
            self.__config.exchange,
            self.__specs,
            dlx=self.__config.dlx,
            declare_exchanges=self.__config.declare_exchanges
        )
