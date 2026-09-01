# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
import time

import pytest

import requests

from tol.rabbitmq import RabbitmqConfig
from tol.rabbitmq.connection import RabbitmqConnection
from tol.rabbitmq.consumer import MessageConsumer
from tol.rabbitmq.handlers import notification_handler
from tol.rabbitmq.schema import NotificationChannel


@pytest.fixture(scope='module')
def config():
    """Return a `RabbitmqConfig` instance from environment variables"""
    return RabbitmqConfig.from_env()


@pytest.fixture(scope='module')
def api_url():
    """Return the base URL for the notification API."""
    if 'LOCALHOST' in os.environ:
        return 'http://localhost:9025'
    return 'http://system-test-api-notification:5000'


@pytest.fixture(autouse=True)
def purge_queue(config):
    """Purge all messages from the RabbitMQ queue."""
    requests.delete(
        f'{config.management_url}'
        f'/api/queues/%2F/{config.queue}/contents',
        auth=(config.username, config.password),
        timeout=10
    )

    yield


def _poll_messages(config, timeout=10):
    """Poll the management API until a message is visible."""
    url = (
        f'{config.management_url}'
        f'/api/queues/%2F/{config.queue}/get'
    )
    payload = {
        'count': 1,
        'ackmode': 'ack_requeue_true',
        'encoding': 'auto'
    }

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        response = requests.post(
            url,
            json=payload,
            auth=(config.username, config.password),
            timeout=10
        )

        response.raise_for_status()

        if messages := response.json():
            return messages

        time.sleep(0.5)

    raise TimeoutError('no message visible on queue')


def _request_body(notification_id, **overrides):
    """Return a notification request body with optional overrides."""
    base = {
        'id': notification_id,
        'channels': ['email'],
        'type': 'system_test',
        'recipients': [{'email': 'test1@example.com'}],
        'context': {'key': 'value'}
    }
    base.update(overrides)
    return base


class TestNotificationSystem:
    def test_post_valid_request_lands_on_queue(self, config, api_url):
        """
        Post a valid notification request and ensure it
        lands on the RabbitMQ queue.
        """
        body = _request_body('system-notification-1')

        response = requests.post(
            f'{api_url}/notification', json=body, timeout=10
        )

        assert response.status_code == 202
        assert response.json() == {
            'notification_id': 'system-notification-1'
        }

        messages = _poll_messages(config)
        assert messages[0]['properties']['message_id'] == (
            'system-notification-1'
        )

    def test_post_then_consume(self, config, api_url):
        """
        Post a notification request and then consume
        it from the RabbitMQ queue.
        """
        body = _request_body(
            'system-notification-2',
            channels=['email', 'slack'],
            recipients=[{'email': 'nowrequired@example.com',
                         'user_id': 'user_1'}]
        )
        requests.post(
            f'{api_url}/notification', json=body, timeout=10
        ).raise_for_status()

        _poll_messages(config)

        received = []
        consumer = MessageConsumer(
            RabbitmqConnection(config),
            config.queue,
            {
                'notification': notification_handler({
                    NotificationChannel.EMAIL: received.append,
                    NotificationChannel.SLACK: received.append
                })
            }
        )
        consumer.process_one()

        assert len(received) == 2
        assert {d.notification_id for d in received} == {
            'system-notification-2'
        }
        assert {d.channel for d in received} == {
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK
        }

    def test_post_invalid_request_returns_400(self, api_url):
        """Post an invalid notification request and expect a 400 response."""
        body = _request_body(
            'system-notification-3',
            recipients=[]
        )

        response = requests.post(
            f'{api_url}/notification', json=body, timeout=10
        )

        assert response.status_code == 400
