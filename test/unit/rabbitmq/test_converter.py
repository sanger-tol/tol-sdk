# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pika.spec import Basic

from pydantic import ValidationError

import pytest

from tol.core import DataSource, core_data_object
from tol.rabbitmq.converter import (
    DefaultMessageToObjectConverter,
    DefaultObjectToMessageConverter
)
from tol.rabbitmq.schema import MessageEnvelope

ENVELOPE = MessageEnvelope.model_validate({
    'id': 'message-1',
    'type': 'test',
    'source': 'portal',
    'created_at': '2026-10-06T12:00:00Z',
    'correlation_id': 'c-1',
    'context': {'answer': 42}
})


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['bus_message', 'output_message']

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


def _receive(data_object_factory, body, routing_key='notify.portal.test'):
    """Convert a received body into an `output_message`."""
    method = Basic.Deliver(routing_key=routing_key, redelivered=True)
    return DefaultMessageToObjectConverter(data_object_factory).convert(
        (method, body)
    )


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


class TestDefaultMessageToObjectConverter:
    def test_unwraps_envelope(self, data_object_factory):
        """Envelope fields and delivery info become attributes."""
        obj = _receive(data_object_factory, ENVELOPE.model_dump_json().encode())

        assert obj.type == 'output_message'
        assert obj.id == 'message-1'
        assert obj.message_type == 'test'
        assert obj.version == 1
        assert obj.context == {'answer': 42}
        assert obj.source == 'portal'
        assert obj.correlation_id == 'c-1'
        assert obj.routing_key == 'notify.portal.test'
        assert obj.redelivered is True

    def test_round_trip(self, data_object_factory):
        """What the outbound converter publishes, the inbound one reads."""
        sent = data_object_factory(
            'bus_message',
            id_='message-1',
            attributes={'message_type': 'test', 'context': {'answer': 42}}
        )
        body, _ = DefaultObjectToMessageConverter(source='portal').convert(sent)

        received = _receive(data_object_factory, body.encode())

        assert received.id == 'message-1'
        assert received.message_type == 'test'
        assert received.context == {'answer': 42}
        assert received.source == 'portal'

    @pytest.mark.parametrize('body', [b'not json', b'{"not": "an envelope"}'])
    def test_invalid_body_raises(self, data_object_factory, body):
        """A body that is not an envelope raises ValidationError."""
        with pytest.raises(ValidationError):
            _receive(data_object_factory, body)
