# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
import os

import pytest

import requests

from tol.rabbitmq.schema import NotificationChannel

from . import fakes
from .broker import peek_messages, wait_for_depth
from .constants import QUEUE


@pytest.fixture(scope='module')
def api_url():
    """Return the base URL for the notification API."""
    if 'LOCALHOST' in os.environ:
        return 'http://localhost:9025'
    return 'http://system-test-api-notification:5000'


def _post(api_url, doc):
    """POST a JSON:API insert document to the bus_message endpoint."""
    return requests.post(
        f'{api_url}/data/bus_message:insert', json=doc, timeout=10
    )


def _insert_doc(notification_id, **overrides):
    """Return an insert document; keyword arguments override the request."""
    context = {
        'id': notification_id,
        'channels': ['email'],
        'type': 'system_test',
        'recipients': [{'email': 'test1@example.com'}],
        'context': {'key': 'value'}
    }
    context.update(overrides)

    return {
        'data': [{
            'type': 'bus_message',
            'id': notification_id,
            'attributes': {
                'message_type': 'notification',
                'context': context
            }
        }]
    }


def _attributes(doc):
    """Return the attributes of the single resource in an insert doc."""
    return doc['data'][0]['attributes']


class TestNotificationApi:
    def test_post_lands_on_queue_with_server_source(self, config, api_url):
        """A valid insert is published under the server's app name."""
        doc = _insert_doc('system-notification-1')
        _attributes(doc)['source'] = 'spoofed'

        response = _post(api_url, doc)

        assert response.status_code == 200
        assert response.json() == {'success': True}

        wait_for_depth(config, QUEUE, 1)
        (message,) = peek_messages(config, QUEUE, count=1)
        assert message['properties']['message_id'] == 'system-notification-1'
        assert json.loads(message['payload'])['source'] == config.app_name

    def test_post_then_consume(self, config, api_url, datasource):
        """A posted notification is fanned out by the consumer."""
        doc = _insert_doc(
            'system-notification-2',
            channels=['email', 'slack'],
            recipients=[{'email': 'nowrequired@example.com',
                         'user_id': 'user_1'}]
        )

        _post(api_url, doc).raise_for_status()
        wait_for_depth(config, QUEUE, 1)

        received = []
        datasource.consume(
            {
                'notification': fakes.notification_handler_spec(
                    email=received, slack=received
                )
            },
            time_limit=5
        )

        assert len(received) == 2
        assert {d.notification_id for d in received} == {
            'system-notification-2'
        }
        assert {d.channel for d in received} == {
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK
        }

    def test_invalid_context_returns_400(self, api_url):
        """A non-dict context is rejected and the object named."""
        doc = _insert_doc('system-notification-3')
        _attributes(doc)['context'] = 'not a dict'

        response = _post(api_url, doc)

        assert response.status_code == 400
        assert 'system-notification-3' in (
            response.json()['errors'][0]['detail']
        )

    def test_email_recipient_without_address_returns_400(self, api_url):
        """The fat-message rule is enforced on the HTTP path."""
        doc = _insert_doc(
            'system-notification-4', recipients=[{'user_id': 'user_1'}]
        )

        response = _post(api_url, doc)

        assert response.status_code == 400

    def test_unknown_target_app_returns_422(self, api_url):
        """A target app with no bound queue is rejected, not dropped."""
        doc = _insert_doc('system-notification-5')
        _attributes(doc)['target_app'] = 'nobody'

        response = _post(api_url, doc)

        assert response.status_code == 422
