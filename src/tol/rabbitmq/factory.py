# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .config import RabbitmqConfig
from .connection import RabbitmqConnection
from .converter import (DefaultMessageToObjectConverter,
                        DefaultObjectToMessageConverter)
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
        to_message_converter_factory=DefaultObjectToMessageConverter,
        to_object_converter_factory=DefaultMessageToObjectConverter
    )

    core_data_object(ds)
    return ds
