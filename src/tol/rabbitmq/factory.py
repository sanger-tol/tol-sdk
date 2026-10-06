# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .config import RabbitmqConfig
from .connection import QueueSpec, RabbitmqConnection
from .converter import DefaultObjectToMessageConverter
from .rabbitmq_datasource import RabbitmqDataSource
from ..core import core_data_object


def create_rabbitmq_datasource(config: RabbitmqConfig) -> RabbitmqDataSource:
    """
    Create a `RabbitmqDataSource` wired with default converters and connection.
    """
    def connection_factory(
        specs: list[QueueSpec] | None = None
    ) -> RabbitmqConnection:
        """Create a connection; `specs` declares queues (consumers only)."""
        return RabbitmqConnection(config, specs=specs)

    def converter_factory() -> DefaultObjectToMessageConverter:
        """Create a converter stamping messages with this app as source."""
        return DefaultObjectToMessageConverter(source=config.app_name)

    ds = RabbitmqDataSource(
        config=config,
        connection_factory=connection_factory,
        to_message_converter_factory=converter_factory
    )

    core_data_object(ds)
    return ds
