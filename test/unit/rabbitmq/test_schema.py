# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pydantic import ValidationError

import pytest

from tol.rabbitmq.schema import (
    MessageEnvelope,
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


class TestMessageEnvelope:
    def test_round_trip(self):
        """
        Test that a MessageEnvelope can be
        round-tripped through model validation.
        """
        envelope = MessageEnvelope.model_validate({
            'id': 'env-1',
            'type': 'send_confirmation',
            'context': {'user': 'me'}
        })
        assert envelope.version == 1

    def test_requires_type_and_context(self):
        """
        Test that a MessageEnvelope requires both 'type' and 'context' fields.
        """
        with pytest.raises(ValidationError):
            MessageEnvelope.model_validate({'id': 'env-1'})


class TestEmailChannelRequiresEmails:
    def test_email_channel_without_email_raises(self):
        """
        Test that a NotificationRequest with the email channel
        and recipients missing emails raises a ValidationError.
        """
        with pytest.raises(ValidationError):
            NotificationRequest.model_validate({
                'id': 'n-1',
                'channels': ['email'],
                'type': 'test',
                'recipients': [{'user_id': 'i_have_no_email'}],
                'context': {}
            })

    def test_slack_channel_allows_missing_email(self):
        """
        Test that a NotificationRequest with the slack channel
        allows recipients to have missing emails.
        """
        request = NotificationRequest.model_validate({
            'id': 'n-2',
            'channels': ['slack'],
            'type': 'test',
            'recipients': [{'user_id': 'slacker'}],
            'context': {}
        })
        assert request.recipients[0].email is None

    def test_email_channel_with_all_emails_passes(self):
        """
        Test that a NotificationRequest with the email channel
        and all recipients having emails passes validation.
        """
        request = NotificationRequest.model_validate({
            'id': 'n-3',
            'channels': ['email', 'slack'],
            'type': 'test',
            'recipients': [
                {'email': 'a@example.com'},
                {'user_id': 'user_2', 'email': 'b@example.com'}
            ],
            'context': {}
        })

        assert len(request.recipients) == 2
        assert all(r.email for r in request.recipients)

    def test_email_channel_with_empty_email_raises(self):
        """
        Test that a NotificationRequest with the email channel
        and a recipient with an empty email raises a ValidationError.
        """
        with pytest.raises(ValidationError):
            NotificationRequest.model_validate({
                'id': 'n-4',
                'channels': ['email'],
                'type': 'test',
                'recipients': [{'email': ''}],
                'context': {}
            })
