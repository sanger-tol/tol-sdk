# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

import requests

from tol.rabbitmq import NotificationRequest
from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.consumer import NotificationConsumer
from tol.rabbitmq.schema import NotificationChannel


@pytest.fixture
def received():
    """Return a list to which dispatched notifications will be appended"""
    return []


def _queue_depth(config):
    """Return the number of messages in the RabbitMQ queue"""
    response = requests.get(
        f'{config.management_url}/api/queues/%2F/{config.queue}',
        auth=(config.username, config.password),
        timeout=10
    )
    response.raise_for_status()
    return response.json().get('messages', 0)


def _publish(datasource, body, message_id):
    """Publish a message to the RabbitMQ queue"""
    message = datasource.data_object_factory(
        'notification_message',
        id_=message_id,
        attributes={'body': body}
    )
    list(datasource.insert_batch('notification_message', [message]))


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
                {'user_id': 'user_2'}
            ],
            'context': {'key': 'value'}
        })

        _publish(
            datasource,
            request.model_dump(mode='json'),
            'notification-1'
        )

        dispatchers = {
            NotificationChannel.EMAIL: received.append,
            NotificationChannel.SLACK: received.append
        }

        consumer = NotificationConsumer(
            RabbitmqConnection(config),
            config.queue,
            dispatchers
        )

        consumer.process_one()

        assert len(received) == 4
        assert {d.notification_id for d in received} == {'notification-1'}
        assert {d.channel for d in received} == {
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK
        }
        assert len({d.delivery_id for d in received}) == 4
        assert _queue_depth(config) == 0

    def test_invalid_payload_nacked(
        self,
        config,
        datasource,
        received
    ):
        """Test that an invalid notification payload is nacked"""
        _publish(datasource, {'not': 'a notification'}, 'bad-1')

        consumer = NotificationConsumer(
            RabbitmqConnection(config),
            config.queue,
            {NotificationChannel.EMAIL: received.append}
        )

        consumer.process_one()

        assert received == []
        assert _queue_depth(config) == 0
