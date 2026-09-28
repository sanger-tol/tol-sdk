# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

import pytest

from tol.core import DataSource, core_data_object
from tol.rabbitmq.converter import DefaultObjectToMessageConverter


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['bus_message']

    @property
    def attribute_types(self):
        raise NotImplementedError()


@pytest.fixture
def data_object_factory():
    """Fixture to provide a DataObject factory for creating test messages."""
    datasource = _MockDataSource(config={})
    core_data_object(datasource)
    return datasource.data_object_factory


def _message(data_object_factory, headers=None):
    """Create a `bus_message` with a valid envelope body."""
    return data_object_factory(
        'bus_message',
        id_='message-1',
        attributes={
            'body': {
                'id': 'message-1',
                'type': 'test',
                'context': {'answer': 42}
            },
            'headers': headers
        }
    )


class TestDefaultObjectToMessageConverter:
    def test_convert_serialises_body_and_properties(
        self,
        data_object_factory,
        monkeypatch
    ):
        """
        Test that the converter serialises the body and sets
        the AMQP properties from the object and envelope
        """
        monkeypatch.setattr(
            'tol.rabbitmq.converter.time.time',
            lambda: 1700000000.5
        )
        message = _message(data_object_factory, headers={'source': 'unit'})

        serialised_body, properties = (
            DefaultObjectToMessageConverter().convert(message)
        )

        assert json.loads(serialised_body) == message.body
        assert properties.content_type == 'application/json'
        assert properties.delivery_mode == 2
        assert properties.message_id == 'message-1'
        assert properties.type == 'test'
        assert properties.timestamp == 1700000000
        assert properties.app_id is None
        assert properties.headers == {'source': 'unit'}

    def test_convert_stamps_app_id(self, data_object_factory):
        """Test that a configured app_id is set on the properties."""
        message = _message(data_object_factory)

        _, properties = (
            DefaultObjectToMessageConverter(app_id='portal').convert(message)
        )

        assert properties.app_id == 'portal'
