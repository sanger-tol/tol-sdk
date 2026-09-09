# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

import pika

from .schema import generate_unique_id
from ..core import DataObject
from ..core.core_converter import Converter

PublishMessage = tuple[str, pika.BasicProperties]
"""The (body, properties) pair passed to `channel.basic_publish`."""

ObjectToMessageConverter = Converter[DataObject, PublishMessage]
"""Converts a `DataObject` into a publishable AMQP message."""


class DefaultObjectToMessageConverter(ObjectToMessageConverter):
    """Serialises a `NotificationMessageObject` to a JSON AMQP message."""

    def convert(self, input_: DataObject) -> PublishMessage:
        """Convert a `NotificationMessageObject` to a JSON AMQP message."""
        body = json.dumps(input_.body)
        properties = pika.BasicProperties(
            content_type='application/json',
            delivery_mode=2,  # persistent
            message_id=input_.id or generate_unique_id(),
            headers=input_.headers,
        )

        return body, properties
