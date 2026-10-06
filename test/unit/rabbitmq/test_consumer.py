# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import signal
from unittest.mock import Mock, PropertyMock, create_autospec

import pika.exceptions
from pika.spec import Basic

import pytest

from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.consumer import MessageConsumer


@pytest.fixture
def mock_connection(mock_channel):
    """Create a mock RabbitmqConnection for testing."""
    connection = create_autospec(RabbitmqConnection, spec_set=True)
    type(connection).channel = PropertyMock(return_value=mock_channel)
    return connection


@pytest.fixture
def on_message():
    """The callback each delivery is passed to."""
    return Mock()


@pytest.fixture
def consumer(mock_connection, on_message):
    """Create a MessageConsumer with a mock callback."""
    return MessageConsumer(mock_connection, 'notification', on_message)


@pytest.fixture
def restore_signal_handlers():
    """Restore original signal handlers after the test."""
    original_int = signal.getsignal(signal.SIGINT)
    original_term = signal.getsignal(signal.SIGTERM)

    yield

    signal.signal(signal.SIGINT, original_int)
    signal.signal(signal.SIGTERM, original_term)


def _on_message(consumer, mock_channel, body=b'{}', delivery_tag=42):
    """Invoke the private message callback directly; returns the method."""
    callback = consumer._MessageConsumer__on_message
    method = Basic.Deliver(delivery_tag=delivery_tag)
    callback(mock_channel, method, Mock(), body)
    return method


class TestMessageConsumer:
    def test_success_acks(self, consumer, mock_channel, on_message):
        """The delivery is passed on and acked when the callback returns."""
        method = _on_message(consumer, mock_channel, b'body')

        on_message.assert_called_once_with(method, b'body')
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=42)
        mock_channel.basic_nack.assert_not_called()

    def test_failure_nacks(self, consumer, mock_channel, on_message):
        """A raising callback nacks without requeue (dead queue)."""
        on_message.side_effect = RuntimeError('smtp down')

        _on_message(consumer, mock_channel)

        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag=42,
            requeue=False
        )
        mock_channel.basic_ack.assert_not_called()


class TestStartStop:
    def test_start_consumes(
        self,
        consumer,
        mock_connection,
        mock_channel,
        restore_signal_handlers
    ):
        """start() connects, consumes and closes when the loop exits."""
        consumer.start()

        mock_connection.connect.assert_called_once()
        mock_channel.basic_qos.assert_called_once_with(prefetch_count=1)
        assert (
            mock_channel.basic_consume.call_args.kwargs['queue']
            == 'notification'
        )
        mock_channel.start_consuming.assert_called_once()
        mock_connection.close.assert_called_once()

    def test_start_closes_on_connection_loss(
        self,
        consumer,
        mock_connection,
        mock_channel,
        restore_signal_handlers
    ):
        """A consume-loop error still closes, then propagates."""
        mock_channel.start_consuming.side_effect = (
            pika.exceptions.StreamLostError('gone')
        )

        with pytest.raises(pika.exceptions.StreamLostError):
            consumer.start()

        mock_connection.close.assert_called_once()

    def test_signal_requests_threadsafe_stop(
        self,
        consumer,
        mock_connection,
        mock_channel,
        restore_signal_handlers
    ):
        """
        SIGTERM schedules stop_consuming on the ioloop instead of calling
        it directly, and does not close the connection itself.
        """
        connection_events = Mock()
        type(mock_channel).connection = PropertyMock(
            return_value=connection_events
        )
        consumer.start()
        mock_connection.close.reset_mock()

        handler = signal.getsignal(signal.SIGTERM)
        assert callable(handler)
        handler(signal.SIGTERM, None)

        connection_events.add_callback_threadsafe.assert_called_once_with(
            mock_channel.stop_consuming
        )
        mock_channel.stop_consuming.assert_not_called()
        mock_connection.close.assert_not_called()

    def test_stop_without_start_is_noop(self, consumer, mock_connection):
        """stop() before start() does nothing."""
        consumer.stop()

        mock_connection.close.assert_not_called()

    def test_process_one_times_out(
        self,
        consumer,
        mock_connection,
        mock_channel
    ):
        """No delivery within the time limit returns False and closes."""
        connection_events = Mock()
        type(mock_channel).connection = PropertyMock(
            return_value=connection_events
        )

        assert consumer.process_one() is False

        connection_events.process_data_events.assert_called_once_with(
            time_limit=5
        )
        mock_connection.close.assert_called_once()

    def test_process_one_handles_message(
        self,
        consumer,
        mock_connection,
        mock_channel,
        on_message
    ):
        """A delivered message returns True."""
        connection_events = Mock()
        connection_events.process_data_events.side_effect = (
            lambda time_limit: _on_message(consumer, mock_channel)
        )
        type(mock_channel).connection = PropertyMock(
            return_value=connection_events
        )

        assert consumer.process_one() is True

        on_message.assert_called_once()
        mock_connection.close.assert_called_once()
