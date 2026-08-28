# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from collections.abc import Callable, Iterable
from typing import Any, Optional

import pika.exceptions

import requests

from .config import RabbitmqConfig
from .connection import RabbitmqConnection
from .converter import MessageToObjectConverter, ObjectToMessageConverter
from ..core import (DataObject, DataSource, DataSourceError, DataSourceFilter,
                    ErrorObject, ReqFieldsTree)
from ..core.operator import DetailGetter, Inserter, ListGetter

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession


class RabbitmqDataSource(DataSource, Inserter, DetailGetter, ListGetter):
    """
    A `DataSource` backed by a RabbitMQ broker.

    Publishes messages via AMQP (`Inserter`) and browses the queue
    via the RabbitMQ Management HTTP API (`DetailGetter` / `ListGetter`).

    Most users should use `create_rabbitmq_datasource()` rather than
    instantiating this directly.
    """

    def __init__(
        self,
        config: RabbitmqConfig,
        connection_factory: Callable[[], RabbitmqConnection],
        to_message_converter_factory: Callable[[], ObjectToMessageConverter],
        to_object_converter_factory: Callable[[], MessageToObjectConverter],
    ) -> None:
        self.__config = config
        self.__connection_factory = connection_factory
        self.__to_message = to_message_converter_factory
        self.__to_object = to_object_converter_factory

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
                'headers': 'dict[str, Any]',
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
                            routing_key=self.__config.routing_key,
                            body=body,
                            properties=properties,
                        )
                        results.append(obj)
                    except pika.exceptions.AMQPError as e:
                        results.append(self.__make_error(obj, e))
        except pika.exceptions.AMQPError as e:
            raise DataSourceError(
                title='Connection Error',
                detail=f'Could not connect to RabbitMQ: {e}',
                status_code=500,
            ) from e

        return results

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None,
        requested_tree: ReqFieldsTree | None = None,
        **kwargs: Any,
    ) -> Iterable[Optional[DataObject]]:
        """
        Get an Iterable of `DataObject` instances by their IDs from RabbitMQ.
        """
        self.__validate_object_type(object_type)

        wanted = list(object_ids)
        fetched = self.__fetch_messages()

        by_message_id: dict[str, DataObject] = {}
        for obj in fetched:
            msg_id = getattr(obj, 'id', None)
            if msg_id is not None:
                by_message_id[msg_id] = obj

        return [by_message_id.get(id_) for id_ in wanted]

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None,
        session: Optional[OperableSession] = None,
        requested_fields: list[str] | None = None,
        requested_tree: ReqFieldsTree | None = None,
        **kwargs: Any,
    ) -> Iterable[DataObject]:
        """Get a list of `DataObject` instances from RabbitMQ."""
        self.__validate_object_type(object_type)

        if object_filters is not None:
            raise DataSourceError(
                title='Unsupported Operation',
                detail='RabbitmqDataSource does not support filtering.',
                status_code=400,
            )

        return self.__fetch_messages()

    def __fetch_messages(self) -> list[DataObject]:
        """Fetch messages from the RabbitMQ queue using the Management API."""
        url = (
            f'{self.__config.management_url}'
            f'/api/queues/{self.__config.vhost}/{self.__config.queue}/get'
        )

        payload = {
            'count': self.get_page_size(),
            'ackmode': 'ack_requeue_true',
            'encoding': 'auto',
        }
        auth = (self.__config.username, self.__config.password)

        try:
            response = requests.post(url, json=payload, auth=auth, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise DataSourceError(
                title='Management API Error',
                detail=f'Failed to browse queue: {e}',
                status_code=502,
            ) from e

        converter = self.__to_object()
        return [
            self.data_object_factory(
                'notification_message',
                id_=self.__extract_message_id(message),
                attributes=converter.convert(message)
            )
            for message in response.json()
        ]

    def __extract_message_id(self, msg: dict[str, Any]) -> str | None:
        """
        Extract the message ID from a RabbitMQ management-API message dict.
        """
        props = msg.get('properties') or {}
        return props.get('message_id')

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
