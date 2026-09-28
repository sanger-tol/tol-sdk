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
from .constants import BUS_MESSAGE, ROUTING_KEY_PATTERN
from .converter import ObjectToMessageConverter
from .schema import MessageEnvelope, NotificationRequest
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

    Publishes validated `MessageEnvelope's via AMQP (`Inserter`).

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
        return [BUS_MESSAGE]

    @property
    def attribute_types(self) -> dict[str, dict[str, str]]:
        """Return the attribute types for each supported object type."""
        return {
            BUS_MESSAGE: {
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
    ) -> list[DataObject]:
        """
        Validate whole batch, then publish it with publisher confirms.

        Raises `DataSourceError` on any failures. A failure mid-publish
        leaves earlier messages in the batch already published.
        """
        self.__validate_object_type(object_type)

        batch = [(obj, self.__validate_message(obj)) for obj in objects]

        converter = self.__to_message()

        try:
            with self.__connection_factory() as conn:
                channel = conn.channel
                channel.confirm_delivery()
                for obj, routing_key in batch:
                    self.__publish(channel, converter, obj, routing_key)
        except pika.exceptions.AMQPError as e:
            raise DataSourceError(
                title='Publish Failed',
                detail=f'Could not publish to RabbitMQ: {e!r}',
                status_code=500
            ) from e

        return [obj for obj, _ in batch]

    def __publish(
        self,
        channel: BlockingChannel,
        converter: ObjectToMessageConverter,
        obj: DataObject,
        routing_key: str
    ) -> None:
        """Publish one message; an unbound routing key raises 422."""
        body, properties = converter.convert(obj)
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

    def __validate_message(self, obj: DataObject) -> str:
        """Raises a 400 unless `obj` is a publishable bus message"""
        routing_key = obj.routing_key
        if (
            not isinstance(routing_key, str)
            or not ROUTING_KEY_PATTERN.match(routing_key)
        ):
            raise _bad_request(
                obj,
                f'routing_key {routing_key!r} must be '
                '<category>.<app>.<subtype>'
            )

        try:
            envelope = MessageEnvelope.model_validate(obj.body)
            if envelope.type == 'notification':
                NotificationRequest.model_validate(envelope.context)
        except ValidationError as e:
            raise _bad_request(
                obj,
                str(e.errors(include_url=False, include_input=False))
            ) from e

        if envelope.id != obj.id:
            raise _bad_request(
                obj,
                f'envelope id {envelope.id!r} does not match object id'
            )

        return routing_key

    def __validate_object_type(self, object_type: str) -> None:
        """Validate that the object type is supported by this data source."""
        if object_type != BUS_MESSAGE:
            raise DataSourceError(
                title='Bad Request',
                detail=f'Unsupported object type: {object_type!r}',
                status_code=400
            )
