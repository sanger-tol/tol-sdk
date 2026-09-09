# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .config import RabbitmqConfig
from .connection import QueueSpec, RabbitmqConnection
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

    ds = RabbitmqDataSource(
        config=config,
        connection_factory=connection_factory,
        to_message_converter_factory=DefaultObjectToMessageConverter
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
    bound to `<category>.<app>.*` on the topic exchange.
    """
    if not config.app_name:
        raise ValueError('RabbitmqConfig.app_name is required for a consumer')

    queue = f'{config.app_name}.{category}'
    specs = [
        QueueSpec(
            name=queue,
            binding_keys=(f'{category}.{config.app_name}.*',)
        )
    ]

    connection = RabbitmqConnection(config, specs=specs)
    connection.connect()

    return MessageConsumer(connection, queue, handlers)
