# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pydantic import ValidationError

import pytest

from tol.core import DataSource, core_data_object
from tol.rabbitmq.converter import DefaultObjectToMessageConverter
from tol.rabbitmq.schema import MessageEnvelope


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


def _convert(data_object_factory, **attributes):
    """Convert a `bus_message`; keyword arguments are extra attributes."""
    message = data_object_factory(
        'bus_message',
        id_='message-1',
        attributes={'message_type': 'test', **attributes}
    )
    return DefaultObjectToMessageConverter(source='portal').convert(message)


class TestDefaultObjectToMessageConverter:
    def test_wraps_attributes_in_envelope(self, data_object_factory):
        """The envelope carries the object id, type, context and source."""
        body, _ = _convert(
            data_object_factory,
            context={'answer': 42},
            correlation_id='c-1'
        )

        envelope = MessageEnvelope.model_validate_json(body)
        assert envelope.id == 'message-1'
        assert envelope.type == 'test'
        assert envelope.source == 'portal'
        assert envelope.correlation_id == 'c-1'
        assert envelope.context == {'answer': 42}

    def test_sets_amqp_properties(self, data_object_factory):
        """AMQP properties mirror the envelope."""
        body, properties = _convert(
            data_object_factory, headers={'trace': 'unit'}
        )

        envelope = MessageEnvelope.model_validate_json(body)
        assert properties.content_type == 'application/json'
        assert properties.delivery_mode == 2
        assert properties.message_id == 'message-1'
        assert properties.type == 'test'
        assert properties.app_id == 'portal'
        assert properties.correlation_id is None
        assert properties.timestamp == int(envelope.created_at.timestamp())
        assert properties.headers == {'trace': 'unit'}

    def test_missing_context_defaults_to_empty(self, data_object_factory):
        """A message without context gets an empty one."""
        body, _ = _convert(data_object_factory)

        assert MessageEnvelope.model_validate_json(body).context == {}

    def test_invalid_context_raises(self, data_object_factory):
        """A non-dict context is not a valid envelope."""
        with pytest.raises(ValidationError):
            _convert(data_object_factory, context=['not', 'a', 'dict'])
