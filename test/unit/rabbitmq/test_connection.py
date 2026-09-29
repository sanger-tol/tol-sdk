# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import dataclasses
import ssl
from unittest.mock import Mock, create_autospec

import pytest

from tol.rabbitmq.connection import (
    QueueSpec,
    RabbitmqConnection,
    declare_topology
)


@pytest.fixture
def pika_stub(monkeypatch, mock_channel):
    """Patch pika.BlockingConnection; returns (factory, connection) mocks."""
    mock_pika_connection = Mock()
    mock_pika_connection.is_open = True
    mock_pika_connection.channel.return_value = mock_channel
    mock_blocking = Mock(return_value=mock_pika_connection)
    monkeypatch.setattr(
        'tol.rabbitmq.connection.pika.BlockingConnection',
        mock_blocking
    )
    return mock_blocking, mock_pika_connection


class TestRabbitmqConnection:
    def test_parameters_from_config(self, config, pika_stub):
        """Tuning values from config reach ConnectionParameters"""
        mock_blocking, _ = pika_stub

        RabbitmqConnection(config).connect()

        parameters = mock_blocking.call_args.args[0]
        assert parameters.heartbeat == 60
        assert parameters.blocked_connection_timeout == 30
        assert parameters.socket_timeout == 10
        assert parameters.connection_attempts == 3
        assert parameters.retry_delay == 2
        assert parameters.ssl_options is None

    def test_ssl_uses_ca_file(self, config, pika_stub, monkeypatch):
        """An SSL connection builds its context from the configured CA"""
        create_context = Mock(
            return_value=create_autospec(ssl.SSLContext, instance=True)
        )
        monkeypatch.setattr(
            'tol.rabbitmq.connection.ssl.create_default_context',
            create_context
        )
        config = dataclasses.replace(
            config, use_ssl=True, ca_file='/certs/ca.pem'
        )

        RabbitmqConnection(config).connect()

        create_context.assert_called_once_with(cafile='/certs/ca.pem')

    def test_channel_before_connect_raises(self, config):
        """Using the channel before connect() is a programming error."""
        with pytest.raises(RuntimeError):
            _ = RabbitmqConnection(config).channel

    def test_dead_channel_is_reopened(self, config, pika_stub, mock_channel):
        """An open connection with a closed channel reopens the channel."""
        mock_blocking, mock_pika_connection = pika_stub
        conn = RabbitmqConnection(config)
        conn.connect()

        mock_channel.is_open = False
        conn.connect()

        assert mock_blocking.call_count == 1
        assert mock_pika_connection.channel.call_count == 2
        assert mock_channel.exchange_declare.call_count == 4


class TestDeclareTopology:
    def test_queue_with_dlq(self, mock_channel):
        """A queue and it's dead letter counterpart are created."""
        specs = [
            QueueSpec(
                name='portal.notify',
                binding_keys=('notify.portal.#',)
            )
        ]

        declare_topology(
            mock_channel,
            'tol',
            specs,
            dlx='tol.dlx'
        )

        mock_channel.exchange_declare.assert_any_call(
            exchange='tol',
            exchange_type='topic',
            durable=True
        )
        mock_channel.exchange_declare.assert_any_call(
            exchange='tol.dlx',
            exchange_type='topic',
            durable=True
        )
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
            routing_key='notify.portal.#'
        )
        mock_channel.queue_declare.assert_any_call(
            queue='portal.notify.dead',
            durable=True,
            arguments={'x-max-length': 10_000}
        )
        mock_channel.queue_bind.assert_any_call(
            queue='portal.notify.dead',
            exchange='tol.dlx',
            routing_key='dead.portal.notify'
        )

    def test_no_dlq_when_disabled(self, mock_channel):
        """Ensure the option to not create a dlq is available."""
        specs = [
            QueueSpec(
                name='q',
                binding_keys=('k',),
                dead_letter=False
            )
        ]

        declare_topology(
            mock_channel,
            'tol',
            specs,
            dlx='tol.dlx'
        )

        mock_channel.queue_declare.assert_called_once_with(
            queue='q',
            durable=True,
            arguments=None
        )

    def test_dead_max_length_is_configurable(self, mock_channel):
        """A dlq max length can also be customisable."""
        specs = [
            QueueSpec(
                name='q',
                binding_keys=('notify.q.#',),
                dead_max_length=5
            )
        ]

        declare_topology(mock_channel, 'tol', specs, dlx='tol.dlx')

        mock_channel.queue_declare.assert_any_call(
            queue='q.dead',
            durable=True,
            arguments={'x-max-length': 5}
        )


class TestQueueSpec:
    def test_str_binding_raises(self):
        """A bare string (missing trailing comma) is rejected."""
        with pytest.raises(TypeError):
            QueueSpec(
                name='q',
                binding_keys=('notify.q.#'),  # pyright: ignore[reportArgumentType]
            )
