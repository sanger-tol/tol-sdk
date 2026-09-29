# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
import time

import pytest

import requests

from tol.rabbitmq import RabbitmqConfig
from tol.rabbitmq.connection import QueueSpec, RabbitmqConnection
from tol.rabbitmq.consumer import MessageConsumer
from tol.rabbitmq.handlers import notification_handler
from tol.rabbitmq.schema import (
    NotificationChannel,
    NotificationRequest,
    wrap_in_envelope
)

QUEUE = 'sdk-test.notify'
BINDING_KEY = 'notify.sdk-test.#'
ROUTING_KEY = 'notify.sdk-test.message'


@pytest.fixture(scope='module')
def config():
    """Return a `RabbitmqConfig` instance from environment variables"""
    return RabbitmqConfig.from_env()


@pytest.fixture(scope='module', autouse=True)
def declare_topology(config):
    """
    Declare the notification queue topology before any tests run.
    """
    specs = [QueueSpec(name=QUEUE, binding_keys=(BINDING_KEY,))]
    with RabbitmqConnection(config, specs=specs):
        pass


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
        f'/api/queues/%2F/{QUEUE}/contents',
        auth=(config.username, config.password),
        timeout=10
    )

    yield


def _poll_messages(config, timeout=10):
    """Poll the management API until a message is visible."""
    url = (
        f'{config.management_url}'
        f'/api/queues/%2F/{QUEUE}/get'
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


def _insert_url(api_url):
    """Returns the data_blueprint insert URL for bus messages."""
    return f'{api_url}/data/bus_message:insert'


def _insert_doc(notification_id, **overrides):
    """Returns a JSON:API insert document wrapping a notification."""
    fields = {
        'id': notification_id,
        'channels': ['email'],
        'type': 'system_test',
        'recipients': [{'email': 'test1@example.com'}],
        'context': {'key': 'value'}
    }

    fields.update(overrides)

    request = NotificationRequest.model_validate(fields)

    return {
        'data': [{
            'type': 'bus_message',
            'id': notification_id,
            'attributes': {
                'body': wrap_in_envelope(request),
                'routing_key': ROUTING_KEY
            }
        }]
    }


def _attributes(doc):
    """Return the attributes of the single resource in an insert doc."""
    return doc['data'][0]['attributes']


class TestNotificationSystem:
    def test_post_valid_request_lands_on_queue(self, config, api_url):
        """
        Post a valid notification request and ensure it
        lands on the RabbitMQ queue.
        """
        doc = _insert_doc('system-notification-1')

        response = requests.post(
            _insert_url(api_url), json=doc, timeout=10
        )

        assert response.status_code == 200
        assert response.json() == {'success': True}

        messages = _poll_messages(config)
        assert messages[0]['properties']['message_id'] == (
            'system-notification-1'
        )

    def test_post_then_consume(self, config, api_url):
        """
        Post a notification request and then consume
        it from the RabbitMQ queue.
        """
        doc = _insert_doc(
            'system-notification-2',
            channels=['email', 'slack'],
            recipients=[{'email': 'nowrequired@example.com',
                         'user_id': 'user_1'}]
        )

        requests.post(
            _insert_url(api_url), json=doc, timeout=10
        ).raise_for_status()

        _poll_messages(config)

        received = []
        consumer = MessageConsumer(
            RabbitmqConnection(config),
            QUEUE,
            {
                'notification': notification_handler({
                    NotificationChannel.EMAIL: received.append,
                    NotificationChannel.SLACK: received.append
                })
            }
        )
        assert consumer.process_one()

        assert len(received) == 2
        assert {d.notification_id for d in received} == {
            'system-notification-2'
        }
        assert {d.channel for d in received} == {
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK
        }

    def test_invalid_envelope_returns_400(self, api_url):
        """A body that is not a MessageEnvelope is rejected by the ds."""
        doc = _insert_doc('system-notification-3')
        _attributes(doc)['body'] = {'not': 'an envelope'}

        response = requests.post(_insert_url(api_url), json=doc, timeout=10)

        assert response.status_code == 400
        assert 'system-notification-3' in (
            response.json()['errors'][0]['detail']
        )

    def test_email_recipient_without_address_returns_400(self, api_url):
        """The fat-message rule is enforced on the HTTP path"""
        doc = _insert_doc('system-notification-4')
        _attributes(doc)['body']['context']['recipients'] = [
            {'user_id': 'user_1'}
        ]

        response = requests.post(_insert_url(api_url), json=doc, timeout=10)

        assert response.status_code == 400

    def test_unroutable_key_returns_422(self, api_url):
        """A routing key with no bound queue is rejected, not dropped."""
        doc = _insert_doc('system-notification-5')
        _attributes(doc)['routing_key'] = 'notify.nobody.message'

        response = requests.post(_insert_url(api_url), json=doc, timeout=10)

        assert response.status_code == 422
