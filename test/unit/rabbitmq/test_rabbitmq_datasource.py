# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import dataclasses
from unittest.mock import Mock, PropertyMock, create_autospec

import pika.exceptions

import pytest

from tol.core import DataSourceError, core_data_object
from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.converter import DefaultObjectToMessageConverter
from tol.rabbitmq.rabbitmq_datasource import RabbitmqDataSource
from tol.rabbitmq.schema import MessageEnvelope


@pytest.fixture
def connection_factory(mock_channel):
    """Create a mock connection factory for testing."""
    mock_connection = create_autospec(RabbitmqConnection, spec_set=True)
    mock_connection.__enter__.return_value = mock_connection
    type(mock_connection).channel = PropertyMock(return_value=mock_channel)
    return Mock(return_value=mock_connection)


def _datasource(config, connection_factory):
    """Create a RabbitmqDataSource whose converter stamps config.app_name."""
    ds = RabbitmqDataSource(
        config,
        connection_factory,
        lambda: DefaultObjectToMessageConverter(source=config.app_name)
    )
    core_data_object(ds)
    return ds


@pytest.fixture
def datasource(config, connection_factory):
    """Create a RabbitmqDataSource with mock dependencies for testing."""
    return _datasource(config, connection_factory)


def _message(datasource, message_id='msg-1', **attributes):
    """Create a valid `bus_message`; keyword arguments override attributes."""
    return datasource.data_object_factory(
        'bus_message',
        id_=message_id,
        attributes={'message_type': 'message', 'context': {}, **attributes}
    )


def _notification(message_id, recipients):
    """Return a notification request context with the given recipients."""
    return {
        'id': message_id,
        'channels': ['email'],
        'type': 'unit_test',
        'recipients': recipients,
        'context': {}
    }


def _published(mock_channel, index=0):
    """Return the publish kwargs and decoded envelope of the nth publish."""
    kwargs = mock_channel.basic_publish.call_args_list[index].kwargs
    return kwargs, MessageEnvelope.model_validate_json(kwargs['body'])


class TestConstruction:
    @pytest.mark.parametrize(
        'app_name', ['', 'Portal', 'portal.app', 'portal*', 'portal\n']
    )
    def test_invalid_app_name_raises(self, config, app_name):
        """app_name becomes the envelope source and routing-key default."""
        config = dataclasses.replace(config, app_name=app_name)

        with pytest.raises(ValueError):
            RabbitmqDataSource(config, Mock(), Mock())


class TestObjectTypeValidation:
    def test_insert_batch_bad_type(self, datasource):
        """
        Test that inserting a batch with a bad type raises a DataSourceError.
        """
        with pytest.raises(DataSourceError) as exc_info:
            list(datasource.insert_batch('bad_type', []))
        assert exc_info.value.status_code == 400

    def test_output_message_is_read_only(self, datasource, mock_channel):
        """output_message is supported for consuming, not inserting."""
        obj = datasource.data_object_factory(
            'output_message',
            id_='msg-1',
            attributes={'message_type': 'message'}
        )

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch('output_message', [obj])

        assert exc_info.value.status_code == 400
        mock_channel.basic_publish.assert_not_called()


class TestRoutingKey:
    def test_defaults_to_own_app_and_notify(self, datasource, mock_channel):
        """Without target_app/category, the message goes to this app."""
        datasource.insert_batch('bus_message', [_message(datasource)])

        kwargs, _ = _published(mock_channel)
        assert kwargs['routing_key'] == 'notify.portal.message'

    def test_target_app_and_category(self, datasource, mock_channel):
        """target_app and category override the defaults."""
        obj = _message(datasource, target_app='genome-notes', category='action')

        datasource.insert_batch('bus_message', [obj])

        kwargs, _ = _published(mock_channel)
        assert kwargs['routing_key'] == 'action.genome-notes.message'

    def test_multi_word_message_type(self, datasource, mock_channel):
        """A message_type can span several words."""
        obj = _message(datasource, message_type='sample.received')

        datasource.insert_batch('bus_message', [obj])

        kwargs, _ = _published(mock_channel)
        assert kwargs['routing_key'] == 'notify.portal.sample.received'

    @pytest.mark.parametrize('attribute, value', [
        ('message_type', None),
        ('message_type', ''),
        ('message_type', 'Message'),
        ('message_type', 'sample..received'),
        ('message_type', 'sample.*'),
        ('message_type', 'sample.#'),
        ('target_app', 'genome.notes'),
        ('target_app', 'Portal'),
        ('category', 'notify.x'),
        ('category', '#'),
    ])
    def test_invalid_part_raises_400(
        self,
        datasource,
        mock_channel,
        attribute,
        value
    ):
        """Every routing-key part must be lowercase with no wildcards."""
        obj = _message(datasource, **{attribute: value})

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch('bus_message', [obj])

        assert exc_info.value.status_code == 400
        assert attribute in exc_info.value.detail
        mock_channel.basic_publish.assert_not_called()


class TestEnvelope:
    def test_envelope_built_from_attributes(self, datasource, mock_channel):
        """The datasource stamps source; the caller supplies the rest."""
        obj = _message(datasource, context={'n': 1}, correlation_id='c-1')

        datasource.insert_batch('bus_message', [obj])

        kwargs, envelope = _published(mock_channel)
        assert envelope.id == 'msg-1'
        assert envelope.type == 'message'
        assert envelope.source == 'portal'
        assert envelope.correlation_id == 'c-1'
        assert envelope.context == {'n': 1}
        assert kwargs['properties'].message_id == 'msg-1'
        assert kwargs['properties'].app_id == 'portal'

    def test_caller_cannot_set_source(self, datasource, mock_channel):
        """A `source` attribute is ignored."""
        obj = _message(datasource, source='spoofed')

        datasource.insert_batch('bus_message', [obj])

        _, envelope = _published(mock_channel)
        assert envelope.source == 'portal'

    def test_missing_id_is_generated(self, datasource, mock_channel):
        """An object without an id is published and returned with one."""
        obj = datasource.data_object_factory(
            'bus_message', attributes={'message_type': 'message'}
        )

        (result,) = datasource.insert_batch('bus_message', [obj])

        kwargs, envelope = _published(mock_channel)
        assert result.id
        assert envelope.id == result.id
        assert envelope.context == {}
        assert kwargs['properties'].message_id == result.id

    def test_invalid_context_raises_400(self, datasource, mock_channel):
        """A non-dict context is rejected."""
        obj = _message(datasource, context='not a dict')

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch('bus_message', [obj])

        assert exc_info.value.status_code == 400
        mock_channel.basic_publish.assert_not_called()

    def test_notification_without_email_raises_400(
        self,
        datasource,
        mock_channel
    ):
        """Notification payloads are validated (fat-message rule)."""
        obj = _message(
            datasource,
            message_type='notification',
            context=_notification('msg-1', [{'user_id': 'user-1'}])
        )

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch('bus_message', [obj])

        assert exc_info.value.status_code == 400
        mock_channel.basic_publish.assert_not_called()

    def test_valid_notification_publishes(self, datasource, mock_channel):
        """A notification with every email present is published."""
        obj = _message(
            datasource,
            message_type='notification',
            context=_notification('msg-1', [{'email': 'a@example.com'}])
        )

        datasource.insert_batch('bus_message', [obj])

        mock_channel.basic_publish.assert_called_once()

    def test_one_invalid_object_publishes_nothing(
        self,
        datasource,
        mock_channel,
        connection_factory
    ):
        """Validation is all-or-nothing per batch and names the object."""
        objects = [
            _message(datasource, 'msg-0'),
            _message(datasource, 'msg-1', message_type='Bad'),
            _message(datasource, 'msg-2'),
        ]

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch('bus_message', objects)

        assert exc_info.value.status_code == 400
        assert 'msg-1' in exc_info.value.detail
        connection_factory.assert_not_called()
        mock_channel.basic_publish.assert_not_called()


class TestPublish:
    def test_success(self, datasource, mock_channel):
        """Test successful publication of a batch of messages."""
        objects = [_message(datasource, f'msg-{i}') for i in range(3)]

        results = datasource.insert_batch('bus_message', objects)

        assert results == objects
        mock_channel.confirm_delivery.assert_called_once_with()
        assert mock_channel.basic_publish.call_count == 3

        kwargs, envelope = _published(mock_channel)
        assert kwargs['exchange'] == 'notification'
        assert kwargs['mandatory'] is True
        assert envelope.id == 'msg-0'

        properties = kwargs['properties']
        assert properties.content_type == 'application/json'
        assert properties.delivery_mode == 2
        assert properties.type == 'message'

    def test_unroutable_raises_422(self, datasource, mock_channel):
        """A routing key with no bound queue raises 422."""
        mock_channel.basic_publish.side_effect = (
            pika.exceptions.UnroutableError([])
        )

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch('bus_message', [_message(datasource)])

        assert exc_info.value.status_code == 422
        assert 'msg-1' in exc_info.value.detail

    def test_nack_raises_500(self, datasource, mock_channel):
        """A broker nack raises 500."""
        mock_channel.basic_publish.side_effect = (
            pika.exceptions.NackError([])
        )

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch('bus_message', [_message(datasource)])

        assert exc_info.value.status_code == 500

    def test_connection_failure(self, datasource, connection_factory):
        """Test that a connection failure raises a DataSourceError."""
        mock_connection = connection_factory.return_value
        mock_connection.__enter__.side_effect = (
            pika.exceptions.AMQPError('connection refused')
        )

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch('bus_message', [_message(datasource)])

        assert exc_info.value.status_code == 500

    def test_insert_batches_by_write_batch_size(
        self,
        config,
        connection_factory,
        mock_channel
    ):
        """One connection per write batch."""
        ds = _datasource(
            dataclasses.replace(config, write_batch_size=2),
            connection_factory
        )
        objects = [_message(ds, f'msg-{i}') for i in range(3)]

        results = ds.insert('bus_message', objects)
        assert results is not None

        assert list(results) == objects
        assert connection_factory.call_count == 2
        assert mock_channel.basic_publish.call_count == 3
