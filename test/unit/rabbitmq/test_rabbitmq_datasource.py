# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import dataclasses
import json
from unittest.mock import Mock, PropertyMock, create_autospec

import pika.exceptions

import pytest

from tol.core import DataSourceError, core_data_object
from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.converter import DefaultObjectToMessageConverter
from tol.rabbitmq.rabbitmq_datasource import RabbitmqDataSource

ROUTING_KEY = 'notify.portal.message'


@pytest.fixture
def connection_factory(mock_channel):
    """Create a mock connection factory for testing."""
    mock_connection = create_autospec(RabbitmqConnection, spec_set=True)
    mock_connection.__enter__.return_value = mock_connection
    type(mock_connection).channel = PropertyMock(return_value=mock_channel)
    return Mock(return_value=mock_connection)


@pytest.fixture
def datasource(config, connection_factory):
    """Create a RabbitmqDataSource with mock dependencies for testing."""
    ds = RabbitmqDataSource(
        config,
        connection_factory,
        DefaultObjectToMessageConverter
    )
    core_data_object(ds)
    return ds


def _envelope(message_id, type_='test', context=None):
    """Returns a valid envelope body."""
    return {
        'id': message_id,
        'type': type_,
        'source': 'sdk-test',
        'created_at': '2026-09-29T12:00:00Z',
        'context': context if context is not None else {}
    }


def _notification(message_id, recipients):
    """Returns a notification envelope body with the given recipients."""
    return _envelope(message_id, type_='notification', context={
        'id': message_id,
        'channels': ['email'],
        'type': 'unit_test',
        'recipients': recipients,
        'context': {}
    })


def _message(datasource, message_id, body=None, routing_key=ROUTING_KEY):
    """Create a `bus_message`; defaults to a valid envelope."""
    return datasource.data_object_factory(
        'bus_message',
        id_=message_id,
        attributes={
            'body': body if body is not None else _envelope(message_id),
            'routing_key': routing_key
        }
    )


class TestObjectTypeValidation:
    def test_insert_batch_bad_type(self, datasource):
        """
        Test that inserting a batch with a bad type raises a DataSourceError.
        """
        with pytest.raises(DataSourceError) as exc_info:
            list(datasource.insert_batch('bad_type', []))
        assert exc_info.value.status_code == 400


class TestMessageValidation:
    @pytest.mark.parametrize('routing_key', [
        None,
        '',
        'notification',
        'notify.portal',
        'notify.portal.*',
        'notify.#.message',
        'Notify.portal.message',
        'notify..message'
    ])
    def test_invalid_routing_raises_400(
        self,
        datasource,
        mock_channel,
        routing_key
    ):
        """Routing keys must be >=3 lowercase words with no wildcards"""
        obj = _message(datasource, 'msg-1', routing_key=routing_key)

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch('bus_message', [obj])

        assert exc_info.value.status_code == 400
        mock_channel.basic_publish.assert_not_called()

    def test_multi_word_subtype_is_valid(self, datasource, mock_channel):
        """Subtypes can span several words."""
        obj = _message(
            datasource, 'msg-1', routing_key='notify.portal.sample.received'
        )

        datasource.insert_batch('bus_message', [obj])

        mock_channel.basic_publish.assert_called_once()

    def test_invalid_envelope_raises_400(self, datasource, mock_channel):
        """A body that is not a MessageEnvelope is rejected."""
        obj = _message(datasource, 'msg-1', body={'not': 'an envelope'})

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
        body = _notification('msg-1', [{'user_id': 'user-1'}])
        obj = _message(datasource, 'msg-1', body=body)

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch('bus_message', [obj])

        assert exc_info.value.status_code == 400
        mock_channel.basic_publish.assert_not_called()

    def test_valid_notification_publishes(self, datasource, mock_channel):
        """A notification with every email present is published"""
        body = _notification('msg-1', [{'email': 'a@example.com'}])
        obj = _message(datasource, 'msg-1', body=body)

        datasource.insert_batch('bus_message', [obj])

        mock_channel.basic_publish.assert_called_once()

    def test_id_mismatch_raises_400(self, datasource, mock_channel):
        """The envelope id must equal the object id."""
        obj = _message(datasource, 'msg-1', body=_envelope('other-id'))

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch('bus_message', [obj])

        assert exc_info.value.status_code == 400
        mock_channel.basic_publish.assert_not_called()

    def test_one_invalid_object_publishes_nothing(
        self,
        datasource,
        mock_channel,
        connection_factory
    ):
        """Validation is an all-or-nothing per batch and names the object"""
        objects = [
            _message(datasource, 'msg-0'),
            _message(datasource, 'msg-1', routing_key='bad'),
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
        """Test successful publication of a batch of messages"""
        objects = [_message(datasource, f'msg-{i}') for i in range(3)]

        results = datasource.insert_batch('bus_message', objects)

        assert results == objects
        mock_channel.confirm_delivery.assert_called_once_with()
        assert mock_channel.basic_publish.call_count == 3

        first = mock_channel.basic_publish.call_args_list[0].kwargs
        assert first['exchange'] == 'notification'
        assert first['routing_key'] == ROUTING_KEY
        assert first['mandatory'] is True
        assert json.loads(first['body']) == _envelope('msg-0')

        properties = first['properties']
        assert properties.content_type == 'application/json'
        assert properties.delivery_mode == 2
        assert properties.message_id == 'msg-0'
        assert properties.type == 'test'

    def test_unroutable_raises_422(self, datasource, mock_channel):
        """A routing key with no bound queue raises 422."""
        mock_channel.basic_publish.side_effect = (
            pika.exceptions.UnroutableError([])
        )

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch(
                'bus_message', [_message(datasource, 'msg-1')]
            )

        assert exc_info.value.status_code == 422
        assert 'msg-1' in exc_info.value.detail

    def test_nack_raises_500(self, datasource, mock_channel):
        """A broker nack raises 500."""
        mock_channel.basic_publish.side_effect = (
            pika.exceptions.NackError([])
        )

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch(
                'bus_message', [_message(datasource, 'msg-1')]
            )

        assert exc_info.value.status_code == 500

    def test_connection_failure(self, datasource, connection_factory):
        """Test that a connetion failure raises a DataSourceError."""
        mock_connection = connection_factory.return_value
        mock_connection.__enter__.side_effect = (
            pika.exceptions.AMQPError('connection refused')
        )

        with pytest.raises(DataSourceError) as exc_info:
            datasource.insert_batch(
                'bus_message', [_message(datasource, 'msg-1')]
            )

        assert exc_info.value.status_code == 500

    def test_insert_batches_by_write_batch_size(
        self,
        config,
        connection_factory,
        mock_channel
    ):
        """
        Test that the datasource splits messages by write_batch_size,
        opening one connection per batch.
        """
        config = dataclasses.replace(config, write_batch_size=2)
        ds = RabbitmqDataSource(
            config,
            connection_factory,
            DefaultObjectToMessageConverter
        )
        core_data_object(ds)

        objects = [_message(ds, f'msg-{i}') for i in range(3)]

        results = ds.insert('bus_message', objects)
        assert results is not None

        assert list(results) == objects
        assert connection_factory.call_count == 2
        assert mock_channel.basic_publish.call_count == 3
