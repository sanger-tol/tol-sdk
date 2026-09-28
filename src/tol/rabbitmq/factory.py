# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .config import RabbitmqConfig
from .connection import QueueSpec, RabbitmqConnection
from .constants import NAME_PATTERN
from .consumer import Handler, MessageConsumer
from .converter import DefaultObjectToMessageConverter
from .rabbitmq_datasource import RabbitmqDataSource
from ..core import core_data_object


def create_rabbitmq_datasource(config: RabbitmqConfig) -> RabbitmqDataSource:
    """
    Create a `RabbitmqDataSource` wired with default converters and connection.
    """
    def connection_factory() -> RabbitmqConnection:
        """Create a new `RabbitmqConnection` using the given config."""
        return RabbitmqConnection(config)

    def converter_factory() -> DefaultObjectToMessageConverter:
        """Create a converter stamping messages with the apps id."""
        return DefaultObjectToMessageConverter(app_id=config.app_name or None)

    ds = RabbitmqDataSource(
        config=config,
        connection_factory=connection_factory,
        to_message_converter_factory=converter_factory
    )

    core_data_object(ds)
    return ds


def create_consumer(
    config: RabbitmqConfig,
    handlers: dict[str, Handler],
    category: str = 'notify'
) -> MessageConsumer:
    """
    Create a `MessageConsumer` for this app, declaring its queue topology.

    Requires `config.app_name`; the queue is named `<app>.<category>` and
    bound to `<category>.<app>.#` on the topic exchange.
    """
    for label, value in (('app_name', config.app_name), ('category', category)):
        if not NAME_PATTERN.match(value):
            raise ValueError(
                f'{label} {value!r} must match {NAME_PATTERN.pattern}'
            )

    queue = f'{config.app_name}.{category}'
    specs = [
        QueueSpec(
            name=queue,
            binding_keys=(f'{category}.{config.app_name}.#',)
        )
    ]

    connection = RabbitmqConnection(config, specs=specs)
    connection.connect()

    return MessageConsumer(connection, queue, handlers)
