# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import dataclasses
import json
from unittest.mock import Mock, PropertyMock, create_autospec

import pika.exceptions
from pika.adapters.blocking_connection import BlockingChannel

import pytest

import requests

from tol.core import (
    DataSourceError,
    DataSourceFilter,
    ErrorObject,
    core_data_object
)
from tol.rabbitmq.config import RabbitmqConfig
from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.converter import (
    DefaultMessageToObjectConverter,
    DefaultObjectToMessageConverter
)
from tol.rabbitmq.rabbitmq_datasource import RabbitmqDataSource


@pytest.fixture
def config():
    """Fixture to provide a RabbitmqConfig for testing."""
    return RabbitmqConfig(
        host='rabbitmq-host',
        port=5672,
        username='test-user',
        password='test-password',
        vhost='test-vhost',
        exchange='notification',
        queue='notification',
        routing_key='notification',
        management_url='http://rabbitmq-mgmt:15672'
    )


@pytest.fixture
def mock_channel():
    """Create a mock BlockingChannel for testing."""
    return create_autospec(BlockingChannel, spec_set=True)


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
        DefaultObjectToMessageConverter,
        DefaultMessageToObjectConverter
    )
    core_data_object(ds)
    return ds


def _message(datasource, message_id, body):
    """Create a DataObject representing a notification message."""
    return datasource.data_object_factory(
        'notification_message',
        id_=message_id,
        attributes={'body': body}
    )


def _management_message(message_id, body, payload_encoding='string'):
    """
    Create a mock management API message with the given body and encoding.
    """
    payload = json.dumps(body)
    if payload_encoding == 'base64':
        import base64
        payload = base64.b64encode(payload.encode('utf-8')).decode('ascii')
    return {
        'payload': payload,
        'payload_encoding': payload_encoding,
        'routing_key': 'notification',
        'redelivered': False,
        'properties': {'message_id': message_id}
    }


def _mock_post(monkeypatch, messages):
    """Patch `requests.post` to return the given messages."""
    response = Mock()
    response.json.return_value = messages
    mock_post = Mock(return_value=response)
    monkeypatch.setattr(
        'tol.rabbitmq.rabbitmq_datasource.requests.post',
        mock_post
    )
    return mock_post


class TestObjectTypeValidation:
    def test_insert_batch_bad_type(self, datasource):
        """
        Test that inserting a batch with a bad type raises a DataSourceError.
        """
        with pytest.raises(DataSourceError) as exc_info:
            list(datasource.insert_batch('bad_type', []))
        assert exc_info.value.status_code == 400

    def test_get_by_id_bad_type(self, datasource):
        """
        Test that getting by ID with a bad type raises a DataSourceError.
        """
        with pytest.raises(DataSourceError):
            list(datasource.get_by_id('bad_type', ['msg-1']))

    def test_get_list_bad_type(self, datasource):
        """
        Test that getting a list with a bad type raises a DataSourceError.
        """
        with pytest.raises(DataSourceError):
            list(datasource.get_list('bad_type'))


class TestInsertbatch:
    def test_success(self, datasource, mock_channel):
        """Test successful insertion of a batch of messages."""
        objects = [
            _message(datasource, f'msg-{i}', {'n': i})
            for i in range(3)
        ]

        results = list(
            datasource.insert_batch('notification_message', objects)
        )

        assert results == objects
        assert mock_channel.basic_publish.call_count == 3

        first = mock_channel.basic_publish.call_args_list[0]
        assert first.kwargs['exchange'] == 'notification'
        assert first.kwargs['routing_key'] == 'notification'
        assert json.loads(first.kwargs['body']) == {'n': 0}

        properties = first.kwargs['properties']
        assert properties.content_type == 'application/json'
        assert properties.delivery_mode == 2
        assert properties.message_id == 'msg-0'

    def test_partial_failure(
        self,
        datasource,
        mock_channel
    ):
        """
        Test that if one message fails to publish, the others still succeed
        and the failed message is returned as an ErrorObject.
        """
        mock_channel.basic_publish.side_effect = [
            None,
            pika.exceptions.AMQPError('broker said no'),
            None
        ]
        objects = [
            _message(datasource, f'msg-{i}', {'n': i})
            for i in range(3)
        ]

        results = list(
            datasource.insert_batch('notification_message', objects)
        )

        assert len(results) == 3
        assert results[0] is objects[0]
        assert results[2] is objects[2]

        error = results[1]
        assert isinstance(error, ErrorObject)
        assert error.object_type == 'notification_message'
        assert error.object_id == 'msg-1'
        assert error.object_ is objects[1]
        assert error.http_code == 500

    def test_object_routing_key_overrides_config(
        self,
        datasource,
        mock_channel
    ):
        """
        Test that if a DataObject has a routing_key attribute, it overrides
        the default routing_key in the config when publishing.
        """
        obj = datasource.data_object_factory(
            'notification_message',
            id_='msg-1',
            attributes={
                'body': {'n': 1},
                'routing_key': 'notification.urgent'
            }
        )

        list(datasource.insert_batch('notification_message', [obj]))

        published = mock_channel.basic_publish.call_args.kwargs
        assert published['routing_key'] == 'notification.urgent'
        assert published['exchange'] == 'notification'

    def test_missing_routing_key_falls_back_to_config(
        self,
        datasource,
        mock_channel
    ):
        """
        Test that if a DataObject has no routing_key attribute, the default
        routing_key from the config is used when publishing.
        """
        obj = _message(datasource, 'msg-1', {'n': 1})

        list(datasource.insert_batch('notification_message', [obj]))

        published = mock_channel.basic_publish.call_args.kwargs
        assert published['routing_key'] == 'notification'

    def test_connection_failure(
        self,
        datasource,
        connection_factory
    ):
        """Test that a connection failure raises a DataSourceError."""
        mock_connection = connection_factory.return_value
        mock_connection.__enter__.side_effect = (
            pika.exceptions.AMQPError('connection refused')
        )
        obj = _message(datasource, 'msg-1', {'n': 1})

        with pytest.raises(DataSourceError) as exc_info:
            list(datasource.insert_batch('notification_message', [obj]))

        assert exc_info.value.status_code == 500

    def test_insert_batches_by_write_batch_size(
        self,
        config,
        connection_factory,
        mock_channel
    ):
        """
        Test that if the write_batch_size is set, the datasource splits
        the messages into multiple batches and calls basic_publish for each.
        """
        config = dataclasses.replace(config, write_batch_size=2)
        ds = RabbitmqDataSource(
            config,
            connection_factory,
            DefaultObjectToMessageConverter,
            DefaultMessageToObjectConverter
        )
        core_data_object(ds)

        objects = [
            _message(ds, f'msg-{i}', {'n': i})
            for i in range(3)
        ]

        results = ds.insert('notification_message', objects)
        assert results is not None

        results_list = list(results)
        assert results_list == objects
        assert connection_factory.call_count == 2
        assert mock_channel.basic_publish.call_count == 3


class TestGetById:
    def test_found_and_missing_ids(self, datasource, monkeypatch):
        """
        Test that get_by_id returns DataObjects for found messages and None
        for missing messages, in the order of the requested IDs.
        """
        _mock_post(monkeypatch, [
            _management_message('msg-1', {'n': 1}),
            _management_message('msg-2', {'n': 2})
        ])

        results = list(
            datasource.get_by_id(
                'notification_message',
                ['msg-2', 'unknown-id', 'msg-1']
            )
        )

        assert len(results) == 3
        assert results[0].id == 'msg-2'
        assert results[0].body == {'n': 2}
        assert results[1] is None
        assert results[2].id == 'msg-1'

    def test_management_api_called_correctly(
        self,
        datasource,
        monkeypatch
    ):
        """
        Test that the management API is called correctly when getting by ID.
        """
        mock_post = _mock_post(monkeypatch, [])

        list(datasource.get_by_id('notification_message', ['msg-1']))

        mock_post.assert_called_once_with(
            'http://rabbitmq-mgmt:15672'
            '/api/queues/test-vhost/notification/get',
            json={
                'count': 20,
                'ackmode': 'ack_requeue_true',
                'encoding': 'auto'
            },
            auth=('test-user', 'test-password'),
            timeout=10
        )

    def test_default_vhost_is_url_encoded(
        self,
        config,
        connection_factory,
        monkeypatch
    ):
        """
        Test that the default vhost is URL-encoded in the management API call.
        """
        config = dataclasses.replace(config, vhost='/')
        ds = RabbitmqDataSource(
            config,
            connection_factory,
            DefaultObjectToMessageConverter,
            DefaultMessageToObjectConverter
        )
        core_data_object(ds)
        mock_post = _mock_post(monkeypatch, [])

        list(ds.get_list('notification_message'))

        assert '/api/queues/%2F/notification/get' in (
            mock_post.call_args.args[0]
        )

    def test_management_api_error(self, datasource, monkeypatch):
        """
        Test that if the management API returns
        an error, a DataSourceError is raised.
        """
        response = Mock()
        response.raise_for_status.side_effect = (
            requests.HTTPError('401 Client Error')
        )
        monkeypatch.setattr(
            'tol.rabbitmq.rabbitmq_datasource.requests.post',
            Mock(return_value=response)
        )

        with pytest.raises(DataSourceError) as exc_info:
            list(datasource.get_by_id('notification_message', ['msg-1']))

        assert exc_info.value.status_code == 502


class TestGetList:
    def test_yields_all_messages(self, datasource, monkeypatch):
        """
        Test that get_list yields all messages returned by the management API.
        """
        _mock_post(monkeypatch, [
            _management_message('msg-1', {'n': 1}),
            _management_message('msg-2', {'n': 2},
                                payload_encoding='base64')
        ])

        results = list(datasource.get_list('notification_message'))

        assert [obj.id for obj in results] == ['msg-1', 'msg-2']
        assert [obj.body for obj in results] == [{'n': 1}, {'n': 2}]

    def test_filters_rejected(self, datasource):
        """
        Test that if a DataSourceFilter is provided, it is rejected with a
        DataSourceError, since filtering is not supported for this datasource.
        """
        mock_filter = create_autospec(DataSourceFilter, spec_set=True)

        with pytest.raises(DataSourceError) as exc_info:
            list(datasource.get_list(
                'notification_message',
                object_filters=mock_filter
            ))

        assert exc_info.value.status_code == 400
