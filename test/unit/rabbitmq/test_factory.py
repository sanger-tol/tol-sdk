# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from unittest.mock import Mock, create_autospec

from pika.adapters.blocking_connection import BlockingChannel

from tol.rabbitmq.factory import create_rabbitmq_datasource
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


def test_returns_configured_datasource(monkeypatch, config):
    """
    Test that create_rabbitmq_datasource returns a
    properly configured RabbitmqDataSource.
    """
    mock_blocking, mock_channel = _stub_broker(monkeypatch)

    ds = create_rabbitmq_datasource(config)

    assert isinstance(ds, RabbitmqDataSource)
    assert ds.supported_types == ['notification_message']
    assert ds.write_batch_size == config.write_batch_size

    obj = ds.data_object_factory(
        'notification_message',
        id_='msg-1',
        attributes={'body': {'n': 1}}
    )
    assert obj.id == 'msg-1'

    inserted = ds.insert_batch('notification_message', [obj])
    assert inserted is not None
    list(inserted)

    mock_blocking.assert_called_once()
    parameters = mock_blocking.call_args.args[0]

    assert parameters.host == 'rabbitmq-host'
    assert parameters.port == 5672
    assert parameters.virtual_host == 'test-vhost'
    assert parameters.credentials.username == 'test-user'
    assert parameters.credentials.password == 'test-password'

    mock_channel.exchange_declare.assert_called_once_with(
        exchange='notification',
        exchange_type='topic',
        durable=True
    )
    mock_channel.queue_declare.assert_called_once_with(
        queue='notification',
        durable=True
    )
    mock_channel.queue_bind.assert_called_once_with(
        queue='notification',
        exchange='notification',
        routing_key='notification'
    )
    mock_channel.basic_publish.assert_called_once()

    published = mock_channel.basic_publish.call_args.kwargs
    assert published['exchange'] == 'notification'
    assert published['routing_key'] == 'notification'
    assert json.loads(published['body']) == {'n': 1}
    assert published['properties'].message_id == 'msg-1'
