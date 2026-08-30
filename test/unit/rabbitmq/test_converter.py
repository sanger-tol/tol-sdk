# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import base64
import json

import pytest

import tol.rabbitmq.converter as converter_module
from tol.core import DataSource, core_data_object
from tol.rabbitmq.converter import (
    DefaultMessageToObjectConverter,
    DefaultObjectToMessageConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['notification_message']

    @property
    def attribute_types(self):
        raise NotImplementedError()


@pytest.fixture
def data_object_factory():
    """Fixture to provide a DataObject factory for creating test messages."""
    datasource = _MockDataSource(config={})
    core_data_object(datasource)
    return datasource.data_object_factory


class TestDefaultObjectToMessageConverter:
    def test_convert_serialises_body_and_properties(
        self,
        data_object_factory
    ):
        """
        Test that the DefaultObjectToMessageConverter
        correctly serialises the body and sets properties.
        """
        body = {
            'notification_id': 'notification-1',
            'context': {'answer': 42}
        }
        headers = {'source': 'unit-test'}
        message = data_object_factory(
            'notification_message',
            id_='message-1',
            attributes={
                'body': body,
                'headers': headers
            }
        )

        serialised_body, properties = (
            DefaultObjectToMessageConverter().convert(message)
        )

        assert json.loads(serialised_body) == body
        assert properties.content_type == 'application/json'
        assert properties.delivery_mode == 2
        assert properties.message_id == 'message-1'
        assert properties.headers == headers

    def test_convert_generates_missing_message_id(
        self,
        data_object_factory,
        monkeypatch
    ):
        """
        Test that if a DataObject has no id, the converter generates
        a unique message_id for the properties.
        """
        monkeypatch.setattr(
            converter_module,
            'generate_unique_id',
            lambda: 'generated-message-id'
        )
        message = data_object_factory(
            'notification_message',
            attributes={'body': {'key': 'value'}}
        )

        _, properties = DefaultObjectToMessageConverter().convert(message)

        assert properties.message_id == 'generated-message-id'
        assert properties.headers is None

    def test_round_trip_through_management_message(
        self,
        data_object_factory
    ):
        """
        Test that a DataObject can be converted to a message and back
        to a DataObject with the same attributes.
        """
        object_converter = DefaultObjectToMessageConverter()
        message_converter = DefaultMessageToObjectConverter()

        body = {
            'notification_id': 'notification-1',
            'deliveries': [{'channel': 'email'}]
        }
        headers = {'source': 'unit-test'}
        message = data_object_factory(
            'notification_message',
            id_='message-1',
            attributes={
                'body': body,
                'headers': headers
            }
        )

        payload, properties = object_converter.convert(message)
        attributes = message_converter.convert({
            'payload': payload,
            'payload_encoding': 'string',
            'routing_key': 'notification',
            'redelivered': False,
            'properties': {
                'message_id': properties.message_id,
                'headers': properties.headers
            }

        })

        assert attributes == {
            'body': body,
            'routing_key': 'notification',
            'headers': headers,
            'redelivered': False,
            'message_id': 'message-1'
        }


class TestDefaultMessageToObjectConverter:
    def test_decodes_base64_payload(self):
        """
        Test that a base64-encoded payload is decoded and parsed as JSON.
        """
        body = {'message': 'hello'}
        encoded_payload = base64.b64encode(
            json.dumps(body).encode('utf-8')
        ).decode('ascii')

        attributes = DefaultMessageToObjectConverter().convert({
            'payload': encoded_payload,
            'payload_encoding': 'base64',
            'routing_key': 'notification',
            'redelivered': True,
            'properties': {
                'message_id': 'message-1',
                'headers': {'source': 'unit-test'}
            }
        })

        assert attributes == {
            'body': body,
            'routing_key': 'notification',
            'headers': {'source': 'unit-test'},
            'redelivered': True,
            'message_id': 'message-1'
        }

    def test_returns_raw_string_from_non_json_payload(self):
        """
        Test that if the payload is a string that is not valid JSON,
        the converter returns it as a raw string in the 'body' attribute.
        """
        attributes = DefaultMessageToObjectConverter().convert({
            'payload': 'not JSON',
            'payload_encoding': 'string'
        })

        assert attributes['body'] == 'not JSON'

    def test_missing_optional_fields_default_to_none(self):
        """
        Test that if optional fields are missing from the message,
        the converter sets them to None in the attributes.
        """
        attributes = DefaultMessageToObjectConverter().convert({
            'payload': '{"ok": true}'
        })

        assert attributes == {
            'body': {'ok': True},
            'routing_key': None,
            'headers': None,
            'redelivered': None,
            'message_id': None
        }
