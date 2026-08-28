# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import base64
import json
from typing import Any

import pika

from ..core import DataObject
from ..core.core_converter import Converter
from .schema import generate_unique_id

PublishMessage = tuple[str, pika.BasicProperties]
"""The (body, properties) pair passed to `channel.basic_publish`."""

ObjectToMessageConverter = Converter[DataObject, PublishMessage]
"""Converts a `DataObject` int a publishable AMQP message."""

MessageToObjectConverter = Converter[dict[str, Any], dict[str, Any]]
"""
Converts a RabbitMQ management-API message dict into an
attributes dict suitable for `data_object_factory`.
"""


class DefaultObjectToMessageConverter(ObjectToMessageConverter):
    """Serialises a `NotificationMessageObject` to a JSON AMQP message."""

    def convert(self, input_: DataObject) -> PublishMessage:
        body = json.dumps(input_.body)
        properties = pika.BasicProperties(
            content_type='application/json',
            delivery_mode=2,  # persistent
            message_id=input_.id or generate_unique_id(),
            headers=input_.headers,
        )

        return body, properties


class DefaultMessageToObjectConverter(MessageToObjectConverter):
    """Deserialises a management-API message into attributes for a `DataObject`."""

    def convert(self, input_: dict[str, Any]) -> dict[str, Any]:
        payload = input_['payload']
        if input_.get('payload_encoding') == 'base64':
            payload = base64.b64decode(payload).decode('utf-8')

        properties = input_.get('properties') or {}

        return {
            'body': self.__parse_body(payload),
            'routing_key': input_.get('routing_key'),
            'headers': properties.get('headers'),
            'redelivered': input_.get('redelivered'),
            'message_id': properties.get('message_id')
        }

    def __parse_body(self, payload: str) -> Any:
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return payload
