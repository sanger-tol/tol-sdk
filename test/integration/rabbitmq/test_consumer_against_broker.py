# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.rabbitmq import NotificationRequest
from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.consumer import MessageConsumer
from tol.rabbitmq.handlers import notification_handler
from tol.rabbitmq.schema import NotificationChannel, wrap_in_envelope

from .broker import publish_raw, queue_depth
from .constants import QUEUE, ROUTING_KEY


@pytest.fixture
def received():
    """Return a list to which dispatched notifications will be appended"""
    return []


def _publish(datasource, body, message_id):
    """Publish a validated bus message through the datasource"""
    message = datasource.data_object_factory(
        'bus_message',
        id_=message_id,
        attributes={'body': body, 'routing_key': ROUTING_KEY}
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
        request = NotificationRequest.model_validate({
            'id': 'notification-1',
            'channels': ['email', 'slack'],
            'type': 'test_type',
            'recipients': [
                {'email': 'test1@example.com'},
                {'email': 'nowrequired@example.com', 'user_id': 'user_2'}
            ],
            'context': {'key': 'value'}
        })

        _publish(
            datasource,
            wrap_in_envelope(request),
            'notification-1'
        )

        dispatchers = {
            NotificationChannel.EMAIL: received.append,
            NotificationChannel.SLACK: received.append
        }

        consumer = MessageConsumer(
            RabbitmqConnection(config),
            QUEUE,
            {'notification': notification_handler(dispatchers)}
        )

        assert consumer.process_one()

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

        consumer = MessageConsumer(
            RabbitmqConnection(config),
            QUEUE,
            {'notification': notification_handler(
                {NotificationChannel.EMAIL: received.append}
            )}
        )

        assert consumer.process_one()

        assert received == []
        assert queue_depth(config, QUEUE) == 0
