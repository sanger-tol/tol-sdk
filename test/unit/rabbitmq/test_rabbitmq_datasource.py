# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import dataclasses
import json
from unittest.mock import Mock, PropertyMock, create_autospec

import pika.exceptions

import pytest

from tol.core import (
    DataSourceError,
    ErrorObject,
    core_data_object
)
from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.converter import DefaultObjectToMessageConverter
from tol.rabbitmq.rabbitmq_datasource import RabbitmqDataSource


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


def _message(datasource, message_id, body):
    """Create a DataObject representing a notification message."""
    return datasource.data_object_factory(
        'notification_message',
        id_=message_id,
        attributes={'body': body}
    )


class TestObjectTypeValidation:
    def test_insert_batch_bad_type(self, datasource):
        """
        Test that inserting a batch with a bad type raises a DataSourceError.
        """
        with pytest.raises(DataSourceError) as exc_info:
            list(datasource.insert_batch('bad_type', []))
        assert exc_info.value.status_code == 400


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
            DefaultObjectToMessageConverter
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
