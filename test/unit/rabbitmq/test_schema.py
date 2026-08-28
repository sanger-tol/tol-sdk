# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest
from pydantic import ValidationError

from tol.rabbitmq.schema import (
    NotificationChannel,
    NotificationRequest,
    Recipient,
    create_deliveries
)


def _request(**overrides) -> dict:
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
        r = NotificationRequest.model_validate(_request())
        assert r.id == 'notification-1'
        assert r.channels == [NotificationChannel.EMAIL]

    def test_empty_channels_rejected(self):
        with pytest.raises(ValidationError):
            NotificationRequest.model_validate(_request(channels=[]))

    def test_empty_recipients_rejected(self):
        with pytest.raises(ValidationError):
            NotificationRequest.model_validate(_request(channels=['unsupported_channel']))

    def test_missing_id_rejected(self):
        body = _request()
        del body['id']
        with pytest.raises(ValidationError):
            NotificationRequest.model_validate(body)

    def test_missing_type_rejected(self):
        body = _request()
        del body['type']
        with pytest.raises(ValidationError):
            NotificationRequest.model_validate(body)

    def test_missing_context_rejected(self):
        body = _request()
        del body['context']
        with pytest.raises(ValidationError):
            NotificationRequest.model_validate(body)


class TestCreateDeliveries:
    def test_fan_out(self):
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
        request = NotificationRequest.model_validate(_request(
            recipients=[Recipient(
                user_id='user_3',
                email='test3@example.com'
            )]
        ))
        (delivery, ) = create_deliveries(request)
        assert delivery.recipient.user_id == 'user_3'
        assert delivery.recipient.email == 'test3@example.com'
