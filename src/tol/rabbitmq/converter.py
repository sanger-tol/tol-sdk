# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
import time

import pika

from ..core import DataObject
from ..core.core_converter import Converter

PublishMessage = tuple[str, pika.BasicProperties]
"""The (body, properties) pair passed to `channel.basic_publish`."""

ObjectToMessageConverter = Converter[DataObject, PublishMessage]
"""Converts a `DataObject` into a publishable AMQP message."""


class DefaultObjectToMessageConverter(ObjectToMessageConverter):
    """Serialises a `bus_message` to a JSON AMQP message."""

    def __init__(self, app_id: str | None = None) -> None:
        self.__app_id = app_id

    def convert(self, input_: DataObject) -> PublishMessage:
        """Convert a `bus_message` to a JSON AMQP message."""
        body = input_.body
        if not isinstance(body, dict):
            raise TypeError(
                f'bus_message {input_.id!r}: body must be a dict',
                f'got {type(body).__name__}'
            )
        properties = pika.BasicProperties(
            content_type='application/json',
            delivery_mode=2,  # persistent
            message_id=input_.id,
            type=body['type'],
            app_id=self.__app_id,
            timestamp=int(time.time()),
            headers=input_.headers,
        )

        return json.dumps(input_.body), properties
