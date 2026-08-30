# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pydantic import ValidationError

import pytest

from tol.rabbitmq.schema import (
    NotificationChannel,
    NotificationRequest,
    Recipient,
    create_deliveries
)


def _request(**overrides) -> dict:
    """Return a base notification request dictionary."""
    base = {
        'id': 'notification-1',
        'channels': ['email'],
        'type': 'test_type',
        'recipients': [{'email': 'test1@example.com'}],
        'context': {'key': 'value'}
    }
    base.update(overrides)
    return base


class TestNotificationRequest:
    def test_valid(self):
        """
        Test that a valid notification request
        is accepted and fields are correctly parsed.
        """
        r = NotificationRequest.model_validate(_request())
        assert r.id == 'notification-1'
        assert r.channels == [NotificationChannel.EMAIL]

    def test_empty_recipients_rejected(self):
        """
        Test that a notification request with an empty recipients list
        is rejected with a ValidationError.
        """
        with pytest.raises(ValidationError):
            NotificationRequest.model_validate(_request(recipients=[]))

    def test_unknown_channel_rejected(self):
        """
        Test that a notification request with an unknown channel
        is rejected with a ValidationError.
        """
        with pytest.raises(ValidationError):
            NotificationRequest.model_validate(_request(channels=['unsupported_channel']))

    def test_missing_id_rejected(self):
        """
        Test that a notification request missing the 'id' field
        is rejected with a ValidationError.
        """
        body = _request()
        del body['id']
        with pytest.raises(ValidationError):
            NotificationRequest.model_validate(body)

    def test_missing_type_rejected(self):
        """
        Test that a notification request missing the 'type' field
        is rejected with a ValidationError.
        """
        body = _request()
        del body['type']
        with pytest.raises(ValidationError):
            NotificationRequest.model_validate(body)

    def test_missing_context_rejected(self):
        """
        Test that a notification request missing the 'context' field
        is rejected with a ValidationError.
        """
        body = _request()
        del body['context']
        with pytest.raises(ValidationError):
            NotificationRequest.model_validate(body)


class TestCreateDeliveries:
    def test_fan_out(self):
        """
        Test that deliveries are correctly fanned out to all channels.
        """
        request = NotificationRequest.model_validate(_request(
            channels=['email', 'slack'],
            recipients=[
                {'email': 'test1@example.com'},
                {'email': 'test2@example.com', 'user_id': 'user_2'}
            ],
        ))

        deliveries = create_deliveries(request)

        assert len(deliveries) == 4
        assert [delivery.channel for delivery in deliveries] == [
            NotificationChannel.EMAIL, NotificationChannel.EMAIL,
            NotificationChannel.SLACK, NotificationChannel.SLACK
        ]
        assert {delivery.notification_id
                for delivery in deliveries} == {'notification-1'}
        assert len({delivery.delivery_id for delivery in deliveries}) == 4

    def test_recipient_fields_carried_over(self):
        """
        Test that the recipient fields are
        correctly carried over to the deliveries.
        """
        request = NotificationRequest.model_validate(_request(
            recipients=[Recipient(
                user_id='user_3',
                email='test3@example.com'
            )]
        ))
        (delivery, ) = create_deliveries(request)
        assert delivery.recipient.user_id == 'user_3'
        assert delivery.recipient.email == 'test3@example.com'
