# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pydantic import ValidationError

import pytest

from tol.rabbitmq import create_rabbitmq_datasource
from tol.rabbitmq.handlers import NotificationHandler
from tol.rabbitmq.schema import NotificationChannel

from . import fakes


@pytest.fixture
def data_object_factory(config):
    """The factory of a real, unconnected RabbitmqDataSource."""
    return create_rabbitmq_datasource(config).data_object_factory


def _message(data_object_factory, **request_overrides):
    """Return a received `notification` output_message."""
    request = {
        'id': 'notification-1',
        'channels': ['email', 'slack'],
        'type': 'test_type',
        'recipients': [{'email': 'test1@example.com'}],
        'context': {'key': 'value'}
    }
    request.update(request_overrides)
    return data_object_factory(
        'output_message',
        id_='message-1',
        attributes={'message_type': 'notification', 'context': request}
    )


def _handler(**sinks):
    """A NotificationHandler recording each channel into its sink."""
    return NotificationHandler(NotificationHandler.Config(
        channels=fakes.recording_channels(**sinks)
    ))


class TestNotificationHandler:
    def test_fans_out_and_dispatches(self, data_object_factory):
        """Each channel's dispatcher gets its own delivery."""
        email, slack = [], []

        _handler(email=email, slack=slack).handle(
            _message(data_object_factory)
        )

        (email_delivery,) = email
        assert email_delivery.channel == NotificationChannel.EMAIL
        assert email_delivery.notification_id == 'notification-1'
        assert email_delivery.recipient.email == 'test1@example.com'
        assert email_delivery.type == 'test_type'
        assert email_delivery.context == {'key': 'value'}
        assert email_delivery.delivery_id == 'notification-1:email:0'

        (slack_delivery,) = slack
        assert slack_delivery.channel == NotificationChannel.SLACK
        assert slack_delivery.delivery_id == 'notification-1:slack:0'

    def test_fan_out_per_recipient(self, data_object_factory):
        """Each recipient gets their own delivery."""
        email = []

        _handler(email=email).handle(_message(
            data_object_factory,
            channels=['email'],
            recipients=[
                {'email': 'test1@example.com'},
                {'email': 'test2@example.com'}
            ]
        ))

        assert [d.recipient.email for d in email] == [
            'test1@example.com', 'test2@example.com'
        ]

    def test_missing_dispatcher_raises_before_dispatching(
        self,
        data_object_factory
    ):
        """
        A channel with no dispatcher raises (-> DLQ) and nothing is
        dispatched, so a replay after deploy doesn't duplicate the others.
        """
        email = []

        with pytest.raises(LookupError, match='slack'):
            _handler(email=email).handle(_message(data_object_factory))

        assert email == []

    def test_invalid_request_raises(self, data_object_factory):
        """A context that is not a NotificationRequest is rejected."""
        with pytest.raises(ValidationError):
            _handler(email=[]).handle(
                _message(data_object_factory, recipients=[])
            )

    def test_unknown_channel_raises_at_construction(self):
        """A misspelt channel fails at startup, not on first message."""
        with pytest.raises(ValueError):
            _handler(emial=[])
