# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
import signal
from unittest.mock import Mock, PropertyMock, create_autospec

from pika.spec import Basic

import pytest

from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.consumer import NotificationConsumer
from tol.rabbitmq.schema import NotificationChannel


@pytest.fixture
def mock_connection(mock_channel):
    """Create a mock RabbitmqConnection for testing."""
    connection = create_autospec(RabbitmqConnection, spec_set=True)
    type(connection).channel = PropertyMock(return_value=mock_channel)
    return connection


@pytest.fixture
def email_dispatcher():
    """Create a mock email dispatcher for testing."""
    return Mock()


@pytest.fixture
def slack_dispatcher():
    """Create a mock slack dispatcher for testing."""
    return Mock()


@pytest.fixture
def consumer(mock_connection, email_dispatcher, slack_dispatcher):
    """Create a NotificationConsumer with mock dependencies for testing."""
    return NotificationConsumer(
        mock_connection,
        'notification',
        {
            NotificationChannel.EMAIL: email_dispatcher,
            NotificationChannel.SLACK: slack_dispatcher
        }
    )


@pytest.fixture
def restore_signal_handlers():
    """Restore original signal handlers after the test."""
    original_int = signal.getsignal(signal.SIGINT)
    original_term = signal.getsignal(signal.SIGTERM)

    yield

    signal.signal(signal.SIGINT, original_int)
    signal.signal(signal.SIGTERM, original_term)


def _on_message(consumer, mock_channel, body, delivery_tag=42):
    """Invoke the private message callback directly."""
    callback = consumer._NotificationConsumer__on_message
    method = Basic.Deliver(delivery_tag=delivery_tag)
    callback(mock_channel, method, Mock(), body)


def _request_body(**overrides):
    """
    Create a JSON-encoded notification request body with optional overrides.
    """
    base = {
        'id': 'notification-1',
        'channels': ['email', 'slack'],
        'type': 'test_type',
        'recipients': [{'email': 'test1@example.com'}],
        'context': {'key': 'value'}
    }
    base.update(overrides)
    return json.dumps(base).encode('utf-8')


class TestOnMessage:
    def test_valid_message_dispatches_and_acks(
        self,
        consumer,
        mock_channel,
        email_dispatcher,
        slack_dispatcher
    ):
        """
        Test that a valid message is dispatched
        to the correct dispatchers and acknowledged.
        """
        _on_message(consumer, mock_channel, _request_body())

        email_dispatcher.assert_called_once()
        slack_dispatcher.assert_called_once()

        email_delivery = email_dispatcher.call_args.args[0]
        assert email_delivery.channel == NotificationChannel.EMAIL
        assert email_delivery.notification_id == 'notification-1'
        assert email_delivery.recipient.email == 'test1@example.com'
        assert email_delivery.type == 'test_type'
        assert email_delivery.context == {'key': 'value'}
        assert email_delivery.delivery_id

        slack_delivery = slack_dispatcher.call_args.args[0]
        assert slack_delivery.channel == NotificationChannel.SLACK
        assert (
            slack_delivery.notification_id
            == email_delivery.notification_id
        )
        assert slack_delivery.delivery_id != email_delivery.delivery_id

        mock_channel.basic_ack.assert_called_once_with(delivery_tag=42)
        mock_channel.basic_nack.assert_not_called()

    def test_fan_out_per_recipient(
        self,
        consumer,
        mock_channel,
        email_dispatcher
    ):
        """
        Test that a message with multiple recipients is fanned out
        to each recipient.
        """
        body = _request_body(
            channels=['email'],
            recipients=[
                {'email': 'test1@example.com'},
                {'user_id': 'user_2'}
            ]
        )

        _on_message(consumer, mock_channel, body)

        assert email_dispatcher.call_count == 2
        emails = [
            c.args[0].recipient.email
            for c in email_dispatcher.call_args_list
        ]
        assert emails == ['test1@example.com', None]

    def test_invalid_json_nacks(
        self,
        consumer,
        mock_channel,
        email_dispatcher
    ):
        """
        Test that an invalid JSON message is nacked and not dispatched.
        """
        _on_message(consumer, mock_channel, b'not json')

        email_dispatcher.assert_not_called()
        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag=42,
            requeue=False
        )
        mock_channel.basic_ack.assert_not_called()

    def test_schema_invalid_nacks(
        self,
        consumer,
        mock_channel,
        email_dispatcher
    ):
        """
        Test that a message failing schema validation is
        nacked and not dispatched.
        """
        _on_message(consumer, mock_channel, _request_body(recipients=[]))

        email_dispatcher.assert_not_called()
        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag=42,
            requeue=False
        )
        mock_channel.basic_ack.assert_not_called()

    def test_dispatcher_failure_nacks(
        self,
        consumer,
        mock_channel,
        email_dispatcher,
        slack_dispatcher
    ):
        """
        Test that if a dispatcher raises an exception, the message is nacked.
        """
        email_dispatcher.side_effect = RuntimeError('smtp down')

        _on_message(consumer, mock_channel, _request_body())

        email_dispatcher.assert_called_once()
        slack_dispatcher.assert_not_called()
        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag=42,
            requeue=False
        )
        mock_channel.basic_ack.assert_not_called()

    def test_missing_dispatcher_skips_channel(
        self,
        mock_connection,
        mock_channel,
        email_dispatcher
    ):
        """
        Test that if a channel has no dispatcher, it is skipped
        and the message is still acknowledged.
        """
        consumer = NotificationConsumer(
            mock_connection,
            'notification',
            {NotificationChannel.EMAIL: email_dispatcher}
        )

        _on_message(consumer, mock_channel, _request_body())

        email_dispatcher.assert_called_once()
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=42)
        mock_channel.basic_nack.assert_not_called()


class TestStartStop:
    def test_start_consumes(
        self,
        consumer,
        mock_connection,
        mock_channel,
        restore_signal_handlers
    ):
        """
        Test that starting the consumer sets up the connection,
        begins consuming messages, and registers signal handlers.
        """

        consumer.start()

        mock_connection.connect.assert_called_once()
        mock_channel.basic_qos.assert_called_once_with(prefetch_count=1)
        mock_channel.basic_consume.assert_called_once()
        assert (
            mock_channel.basic_consume.call_args.kwargs['queue']
            == 'notification'
        )
        mock_channel.start_consuming.assert_called_once()

    def test_signal_handlers_stop_consuming(
        self,
        consumer,
        mock_connection,
        mock_channel,
        restore_signal_handlers
    ):
        """
        Test that the signal handlers for SIGINT and SIGTERM
        stop consuming and close the connection.
        """
        consumer.start()

        handler = signal.getsignal(signal.SIGTERM)
        assert callable(handler)

        handler(signal.SIGTERM, None)

        mock_channel.stop_consuming.assert_called_once()
        mock_connection.close.assert_called_once()

    def test_stop_without_start_is_safe(self, consumer, mock_connection):
        """
        Test that calling stop() without start() does not raise an error.
        """
        consumer.stop()

        mock_connection.close.assert_called_once()

    def test_process_one(
        self,
        consumer,
        mock_connection,
        mock_channel
    ):
        """
        Test that process_one() processes a single message and then stops.
        """
        connection_events = Mock()
        type(mock_channel).connection = PropertyMock(
            return_value=connection_events
        )

        consumer.process_one()

        mock_connection.connect.assert_called_once()
        mock_channel.basic_consume.assert_called_once()
        connection_events.process_data_events.assert_called_once_with(
            time_limit=5
        )
        mock_channel.stop_consuming.assert_called_once()
        mock_connection.close.assert_called_once()
