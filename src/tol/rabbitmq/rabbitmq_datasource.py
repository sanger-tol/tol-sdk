# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from collections.abc import Callable, Iterable
from typing import Any, Optional

import pika.exceptions

from .config import RabbitmqConfig
from .connection import RabbitmqConnection
from .converter import ObjectToMessageConverter
from ..core import (DataObject, DataSource, DataSourceError,
                    ErrorObject, ReqFieldsTree)
from ..core.operator import Inserter

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession


class RabbitmqDataSource(DataSource, Inserter):
    """
    A `DataSource` backed by a RabbitMQ broker.

    Publishes messages via AMQP (`Inserter`).

    Most users should use `create_rabbitmq_datasource()` rather than
    instantiating this directly.
    """

    def __init__(
        self,
        config: RabbitmqConfig,
        connection_factory: Callable[[], RabbitmqConnection],
        to_message_converter_factory: Callable[[], ObjectToMessageConverter]
    ) -> None:
        self.__config = config
        self.__connection_factory = connection_factory
        self.__to_message = to_message_converter_factory
        self.write_batch_size = config.write_batch_size

        super().__init__({})

    @property
    def supported_types(self) -> list[str]:
        """Return the list of supported object types for this data source."""
        return ['notification_message']

    @property
    def attribute_types(self) -> dict[str, dict[str, str]]:
        """Return the attribute types for each supported object type."""
        return {
            'notification_message': {
                'body': 'dict[str, Any]',
                'routing_key': 'str',
                'headers': 'dict[str, Any]'
            }
        }

    def insert_batch(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None,
        requested_tree: ReqFieldsTree | None = None,
        **kwargs: Any,
    ) -> Iterable[DataObject | ErrorObject] | None:
        """Insert a batch of objects into RabbitMQ."""
        self.__validate_object_type(object_type)

        converter = self.__to_message()
        results: list[DataObject | ErrorObject] = []

        try:
            with self.__connection_factory() as conn:
                channel = conn.channel
                for obj in objects:
                    try:
                        body, properties = converter.convert(obj)
                        channel.basic_publish(
                            exchange=self.__config.exchange,
                            routing_key=(
                                getattr(obj, 'routing_key', None)
                                or self.__config.routing_key
                            ),
                            body=body,
                            properties=properties,
                        )
                        results.append(obj)
                    except pika.exceptions.AMQPError as e:
                        results.append(self.__make_error(obj, e))
        except pika.exceptions.AMQPError as e:
            raise DataSourceError(
                title='Connection Error',
                detail=f'Could not connect to RabbitMQ: {e!r}',
                status_code=500,
            ) from e

        return results

    def __make_error(
        self,
        obj: DataObject,
        exc: Exception,
    ) -> ErrorObject:
        """
        Create an `ErrorObject` for a failed insertion or operation on a
        `DataObject` of type `notification_message`.
        """
        return ErrorObject(
            details={'exception': str(exc)},
            object_type='notification_message',
            object_id=obj.id,
            object_=obj,
            http_code=500
        )

    def __validate_object_type(self, object_type: str) -> None:
        """Validate that the object type is supported by this data source."""
        if object_type != 'notification_message':
            raise DataSourceError(
                title='Bad Request',
                detail=f'Unsupported object type: {object_type!r}',
                status_code=400
            )
