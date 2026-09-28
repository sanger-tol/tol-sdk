# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import dataclasses
import json
from unittest.mock import Mock, create_autospec

from pika.adapters.blocking_connection import BlockingChannel

import pytest

from tol.rabbitmq.config import RabbitmqConfig
from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.consumer import MessageConsumer
from tol.rabbitmq.factory import create_consumer, create_rabbitmq_datasource
from tol.rabbitmq.rabbitmq_datasource import RabbitmqDataSource


def _stub_broker(monkeypatch):
    """Patch pika so `connect()` succeeds without a real broker."""
    mock_channel = create_autospec(BlockingChannel, spec_set=True)
    mock_pika_connection = Mock()
    mock_pika_connection.channel.return_value = mock_channel
    mock_pika_connection.is_open = True
    mock_blocking = Mock(return_value=mock_pika_connection)
    monkeypatch.setattr(
        'tol.rabbitmq.connection.pika.BlockingConnection',
        mock_blocking
    )
    return mock_blocking, mock_channel


def _bus_message(ds):
    """Create a valid `bus_message` for publishing through factory ds."""
    return ds.data_object_factory(
        'bus_message',
        id_='msg-1',
        attributes={
            'body': {'id': 'msg-1', 'type': 'test', 'context': {}},
            'routing_key': 'notify.portal.message'
        }
    )


def test_returns_configured_datasource(monkeypatch, config):
    """
    Test that create_rabbitmq_datasource returns a
    properly configured RabbitmqDataSource.
    """
    _, mock_channel = _stub_broker(monkeypatch)

    ds = create_rabbitmq_datasource(config)

    assert isinstance(ds, RabbitmqDataSource)
    assert ds.supported_types == ['bus_message']
    assert ds.write_batch_size == config.write_batch_size

    ds.insert_batch('bus_message', [_bus_message(ds)])

    published = mock_channel.basic_publish.call_args.kwargs
    assert published['exchange'] == 'notification'
    assert published['routing_key'] == 'notify.portal.message'
    assert published['mandatory'] is True
    assert json.loads(published['body']) == {
        'id': 'msg-1', 'type': 'test', 'context': {}
    }
    assert published['properties'].message_id == 'msg-1'
    assert published['properties'].app_id is None


def test_app_name_stamped_as_app_id(monkeypatch, config):
    """Test that config.app_name reaches the published app_id"""
    _, mock_channel = _stub_broker(monkeypatch)
    ds = create_rabbitmq_datasource(
        dataclasses.replace(config, app_name='portal')
    )

    ds.insert_batch('bus_message', [_bus_message(ds)])

    properties = mock_channel.basic_publish.call_args.kwargs['properties']
    assert properties.app_id == 'portal'


def _config_with_app():
    """Creates a RabbitmqConfig object with app_name provided"""
    return RabbitmqConfig(
        host='rabbitmq-host',
        port=5672,
        username='test-user',
        password='test-password',
        vhost='test-vhost',
        exchange='tol',
        management_url='http://rabbitmq-mgmt:15672',
        app_name='portal'
    )


class TestCreateConsumer:
    def test_returns_consumer_with_app_queue(self, monkeypatch):
        """
        Test that create_consumer declares the app's queue
        and returns a MessageConsumer bound to it.
        """
        mock_blocking, mock_channel = _stub_broker(monkeypatch)

        consumer = create_consumer(_config_with_app(), {})

        assert isinstance(consumer, MessageConsumer)

        mock_channel.queue_declare.assert_any_call(
            queue='portal.notify',
            durable=True,
            arguments={
                'x-dead-letter-exchange': 'tol.dlx',
                'x-dead-letter-routing-key': 'dead.portal.notify'
            }
        )
        mock_channel.queue_bind.assert_any_call(
            queue='portal.notify',
            exchange='tol',
            routing_key='notify.portal.*'
        )

    def test_empty_app_name_raises(self):
        """Test that create_consumer requires an app name."""
        config = dataclasses.replace(_config_with_app(), app_name='')

        with pytest.raises(ValueError):
            create_consumer(config, {})

    def test_connect_twice_is_idempotent(self, monkeypatch):
        """
        Test that connecting an open connection is a no-op and does nothing.
        """
        mock_blocking, _ = _stub_broker(monkeypatch)

        conn = RabbitmqConnection(_config_with_app())

        conn.connect()
        conn.connect()

        assert mock_blocking.call_count == 1
