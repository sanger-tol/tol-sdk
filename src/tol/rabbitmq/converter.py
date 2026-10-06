# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import UTC, datetime

import pika

from .schema import MessageEnvelope
from ..core import DataObject
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
