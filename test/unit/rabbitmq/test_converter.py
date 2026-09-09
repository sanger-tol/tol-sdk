# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

import pytest

import tol.rabbitmq.converter as converter_module
from tol.core import DataSource, core_data_object
from tol.rabbitmq.converter import (
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
