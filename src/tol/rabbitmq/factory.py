# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..core import core_data_object
from .config import RabbitmqConfig
from .connection import RabbitmqConnection
from .converter import (DefaultMessageToObjectConverter,
                        DefaultObjectToMessageConverter)
from .rabbitmq_datasource import RabbitmqDataSource


def create_rabbitmq_datasource(config: RabbitmqConfig) -> RabbitmqDataSource:
    """
    Create a `RabbitmqDataSource` wired with default converters and connection.

    callers MUST run `core_data_object(ds)` on the returned instance before use
    so that `data_object_factory` is injected.
    """
    def connection_factory() -> RabbitmqConnection:
        return RabbitmqConnection(config)

    ds = RabbitmqDataSource(
        config=config,
        connection_factory=connection_factory,
        to_message_converter_factory=DefaultObjectToMessageConverter,
        to_object_converter_factory=DefaultMessageToObjectConverter
    )
    core_data_object(ds)
    return ds
