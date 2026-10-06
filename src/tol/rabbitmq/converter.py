# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import UTC, datetime

import pika
from pika.spec import Basic

from .constants import OUTPUT_MESSAGE
from .schema import MessageEnvelope
from ..core import DataObject, DataObjectFactory
from ..core.core_converter import Converter

PublishMessage = tuple[str, pika.BasicProperties]
"""The (body, properties) pair passed to `channel.basic_publish`."""

ObjectToMessageConverter = Converter[DataObject, PublishMessage]
"""Converts a `DataObject` into a publishable AMQP message."""


class DefaultObjectToMessageConverter(ObjectToMessageConverter):
    """Wraps a `bus_message` in a `MessageEnvelope` and serialises it."""

    def __init__(self, source: str) -> None:
        self.__source = source

    def convert(self, input_: DataObject) -> PublishMessage:
        """Raises `pydantic.ValidationError` if the attributes are invalid."""
        context = input_.context
        envelope = MessageEnvelope.model_validate({
            'id': input_.id,
            'type': input_.message_type,
            'source': self.__source,
            'created_at': datetime.now(UTC),
            'correlation_id': input_.correlation_id,
            'context': {} if context is None else context,
        })

        properties = pika.BasicProperties(
            content_type='application/json',
            delivery_mode=2,  # persistent
            message_id=envelope.id,
            type=envelope.type,
            app_id=self.__source,
            correlation_id=envelope.correlation_id,
            timestamp=int(envelope.created_at.timestamp()),
            headers=input_.headers,
        )

        return envelope.model_dump_json(), properties


ReceivedMessage = tuple[Basic.Deliver, bytes]
"""The (method, body) pair a consumer receives from the broker."""

MessageToObjectConverter = Converter[ReceivedMessage, DataObject]
"""Converts a received AMPQ message into an `output_message`"""


class DefaultMessageToObjectConverter(MessageToObjectConverter):
    """Unwraps a `MessageEnvelope` into an `output_message`"""

    def __init__(self, data_object_factory: DataObjectFactory) -> None:
        self.__factory = data_object_factory

    def convert(self, input_: ReceivedMessage) -> DataObject:
        """Raises `pydantic.ValidationError` if the body is not an envelope."""
        method, body = input_
        envelope = MessageEnvelope.model_validate_json(body)

        return self.__factory(
            OUTPUT_MESSAGE,
            id_=envelope.id,
            attributes={
                'message_type': envelope.type,
                'version': envelope.version,
                'context': envelope.context,
                'source': envelope.source,
                'created_at': envelope.created_at,
                'correlation_id': envelope.correlation_id,
                'routing_key': method.routing_key,
                'redelivered': method.redelivered
            }
        )
