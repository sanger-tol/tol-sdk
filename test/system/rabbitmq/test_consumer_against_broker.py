# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.rabbitmq.schema import NotificationChannel

from . import fakes
from .broker import publish_raw, queue_depth
from .constants import QUEUE, ROUTING_KEY


@pytest.fixture
def received():
    """Return a list to which dispatched notifications will be appended"""
    return []


def _publish(datasource, message_type, context, message_id):
    """Publish a bus message through the datasource."""
    message = datasource.data_object_factory(
        'bus_message',
        id_=message_id,
        attributes={'message_type': message_type, 'context': context}
    )
    datasource.insert_batch('bus_message', [message])


class TestConsumerAgainstBroker:
    def test_valid_request_dispatches_and_acks(
        self,
        config,
        datasource,
        received
    ):
        """
        Test that a valid notification request is dispatched and acknowledged
        """
        _publish(datasource, 'notification', {
            'id': 'notification-1',
            'channels': ['email', 'slack'],
            'type': 'test_type',
            'recipients': [
                {'email': 'test1@example.com'},
                {'email': 'nowrequired@example.com', 'user_id': 'user_2'}
            ],
            'context': {'key': 'value'}
        }, 'notification-1')

        datasource.consume(
            {
                'notification': fakes.notification_handler_spec(
                    email=received, slack=received
                )
            },
            time_limit=5
        )

        assert len(received) == 4
        assert {d.notification_id for d in received} == {'notification-1'}
        assert {d.channel for d in received} == {
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK
        }
        assert len({d.delivery_id for d in received}) == 4
        assert queue_depth(config, QUEUE) == 0

    def test_invalid_payload_nacked(
        self,
        config,
        datasource,
        received
    ):
        """Test that an invalid notification payload is nacked"""
        publish_raw(config, ROUTING_KEY, {'not': 'a notification'})

        datasource.consume(
            {
                'notification': fakes.notification_handler_spec(
                    email=received
                )
            },
            time_limit=5
        )

        assert received == []
        assert queue_depth(config, QUEUE) == 0
