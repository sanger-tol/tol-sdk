# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from collections.abc import Callable, Iterable
from typing import Any, Optional

import pika.exceptions

from pydantic import ValidationError

from .config import RabbitmqConfig
from .connection import RabbitmqConnection
from .constants import (
    BUS_MESSAGE,
    DEFAULT_CATEGORY,
    NAME_PATTERN,
    OUTPUT_MESSAGE,
    TYPE_PATTERN
)
from .converter import ObjectToMessageConverter, PublishMessage
from .schema import NotificationRequest, generate_unique_id
from ..core import DataObject, DataSource, DataSourceError, ReqFieldsTree
from ..core.operator import Inserter

if typing.TYPE_CHECKING:
    from pika.adapters.blocking_connection import BlockingChannel

    from ..core.session import OperableSession


def _bad_request(obj: DataObject, detail: str) -> DataSourceError:
    """Return a 400 error naming the offending object."""
    return DataSourceError(
        title='Bad Request',
        detail=f'{BUS_MESSAGE} {obj.id!r}: {detail}',
        status_code=400
    )


class RabbitmqDataSource(DataSource, Inserter):
    """
    A `DataSource` backed by a RabbitMQ broker.

    Publishes `bus_message` objects (`Inserter`). Each one is wrapped in a
    `MessageEnvelope` and routed by `<category>.<target_app>.<message_type>`;
    callers never build either.

    Most users should use `create_rabbitmq_datasource()` rather than
    instantiating this directly.
    """

    def __init__(
        self,
        config: RabbitmqConfig,
        connection_factory: Callable[[], RabbitmqConnection],
        to_message_converter_factory: Callable[[], ObjectToMessageConverter]
    ) -> None:
        if not NAME_PATTERN.fullmatch(config.app_name):
            raise ValueError(
                f'app_name {config.app_name!r} must match '
                f'{NAME_PATTERN.pattern}'
            )

        self.__config = config
        self.__connection_factory = connection_factory
        self.__to_message = to_message_converter_factory
        self.write_batch_size = config.write_batch_size

        super().__init__({})

    @property
    def supported_types(self) -> list[str]:
        """Return the list of supported object types for this data source."""
        return [BUS_MESSAGE, OUTPUT_MESSAGE]

    @property
    def attribute_types(self) -> dict[str, dict[str, str]]:
        """Return the attribute types for each supported object type."""
        return {
            BUS_MESSAGE: {
                'message_type': 'str',
                'context': 'dict[str, Any]',
                'target_app': 'str',
                'category': 'str',
                'correlation_id': 'str',
                'headers': 'dict[str, Any]'
            },
            OUTPUT_MESSAGE: {
                'message_type': 'str',
                'version': 'int',
                'context': 'dict[str, Any]',
                'source': 'str',
                'created_at': 'datetime',
                'correlation_id': 'str',
                'routing_key': 'str',
                'redelivered': 'bool'
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
    ) -> list[DataObject]:
        """
        Validate and wrap the whole batch, then publish it with publisher
        confirms. Objects without an id are returned with a generated one.

        Raises `DataSourceError` on any failures. A failure mid-publish
        leaves earlier messages in the batch already published.
        """
        self.__validate_object_type(object_type)

        converter = self.__to_message()
        batch = [self.__prepare(obj, converter) for obj in objects]

        try:
            with self.__connection_factory() as conn:
                channel = conn.channel
                channel.confirm_delivery()
                for obj, routing_key, message in batch:
                    self.__publish(channel, obj, routing_key, message)
        except pika.exceptions.AMQPError as e:
            raise DataSourceError(
                title='Publish Failed',
                detail=f'Could not publish to RabbitMQ: {e!r}',
                status_code=500
            ) from e

        return [obj for obj, _, _ in batch]

    def __prepare(
        self,
        obj: DataObject,
        converter: ObjectToMessageConverter
    ) -> tuple[DataObject, str, PublishMessage]:
        """Return `obj` (with an id), its routing key and message; 400 if invalid."""
        if obj.id is None:
            obj = self.data_object_factory(
                BUS_MESSAGE,
                id_=generate_unique_id(),
                attributes=obj.attributes
            )

        routing_key = self.__routing_key(obj)

        try:
            message = converter.convert(obj)
            if obj.message_type == 'notification':
                NotificationRequest.model_validate(obj.context)
        except ValidationError as e:
            raise _bad_request(
                obj,
                str(e.errors(include_url=False, include_input=False))
            ) from e

        return obj, routing_key, message

    def __routing_key(self, obj: DataObject) -> str:
        """Return `<category>.<target_app>.<message_type>`; 400 if invalid."""
        parts = (
            ('category', obj.category or DEFAULT_CATEGORY, NAME_PATTERN),
            ('target_app', obj.target_app or self.__config.app_name, NAME_PATTERN),
            ('message_type', obj.message_type, TYPE_PATTERN),
        )
        validated: list[str] = []
        for label, value, pattern in parts:
            if not isinstance(value, str) or not pattern.fullmatch(value):
                raise _bad_request(
                    obj,
                    f'{label} {value!r} must match {pattern.pattern}'
                )
            validated.append(value)

        return '.'.join(validated)

    def __publish(
        self,
        channel: BlockingChannel,
        obj: DataObject,
        routing_key: str,
        message: PublishMessage
    ) -> None:
        """Publish one message; an unbound routing key raises 422."""
        body, properties = message
        try:
            channel.basic_publish(
                exchange=self.__config.exchange,
                routing_key=routing_key,
                body=body,
                properties=properties,
                mandatory=True
            )
        except pika.exceptions.UnroutableError as e:
            raise DataSourceError(
                title='Unroutable Message',
                detail=(
                    f'No queue is bound to the routing key '
                    f'{routing_key!r} (id {obj.id!r})'
                ),
                status_code=422
            ) from e

    def __validate_object_type(self, object_type: str) -> None:
        """Only `bus_message` can be inserted. `output_message` is read-only."""
        if object_type != BUS_MESSAGE:
            raise DataSourceError(
                title='Bad Request',
                detail=f'Unsupported object type: {object_type!r}',
                status_code=400
            )
