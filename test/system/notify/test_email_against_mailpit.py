# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
import time

import pytest

import requests

from tol.notify import EmailConfig, EmailSender
from tol.rabbitmq import (
    NotificationHandler,
    RabbitmqConfig,
    create_rabbitmq_datasource
)

MAILPIT_URL = os.environ['MAILPIT_URL']


def _messages():
    """Return mailpit's message summaries, newest first."""
    response = requests.get(f'{MAILPIT_URL}/api/v1/messages', timeout=5)
    response.raise_for_status()
    return response.json()['messages']


def _message(message_id):
    """Return one message in full, including its HTML body."""
    response = requests.get(
        f'{MAILPIT_URL}/api/v1/message/{message_id}', timeout=5
    )
    response.raise_for_status()
    return response.json()


def _wait_for_messages(count, timeout=5.0):
    """Poll until mailpit holds exactly `count` messages."""
    deadline = time.monotonic() + timeout
    while True:
        messages = _messages()
        if len(messages) == count:
            return messages
        if time.monotonic() > deadline:
            raise TimeoutError(
                f'Expected {count} message(s), found {len(messages)}'
            )
        time.sleep(0.1)


@pytest.fixture(autouse=True)
def empty_mailbox():
    """Delete every stored message before each test."""
    requests.delete(
        f'{MAILPIT_URL}/api/v1/messages', timeout=5
    ).raise_for_status()


@pytest.fixture
def sender():
    """A real EmailSender configured from the SMTP_* environment."""
    return EmailSender(EmailConfig.from_env())


@pytest.fixture
def data_object_factory():
    """The factory of a RabbitmqDataSource, for building output_messages."""
    return create_rabbitmq_datasource(RabbitmqConfig.from_env()).data_object_factory


class TestEmailSender:
    def test_delivers_html_email(self, sender):
        """Test that a real SMTP round trip delivers the message intact."""
        sender.send(['lucas@example.com'], 'Hello', '<p>Hi Lucas</p>')

        [summary] = _wait_for_messages(1)
        message = _message(summary['ID'])

        assert message['Subject'] == 'Hello'
        assert message['From']['Address'] == os.environ['SMTP_FROM']
        assert [to['Address'] for to in message['To']] == ['lucas@example.com']
        assert '<p>Hi Lucas</p>' in message['HTML']


class TestNotificationPipeline:
    def test_one_branded_email_per_recipient(self, data_object_factory, tmp_path):
        """Test handler -> dispatcher -> renderer -> SMTP end to end."""
        (tmp_path / 'sample_ready.subject.txt').write_text(
            'Sample {{ sample }} is ready\n'
        )
        (tmp_path / 'sample_ready.body.html').write_text(
            '{% extends "tol_base.html" %}'
            '{% block content %}'
            '<p>{{ sample }} for {{ recipient.email }}</p>'
            '{% endblock %}'
        )

        handler = NotificationHandler(NotificationHandler.Config(channels={
            'email': {
                'module': 'tol.rabbitmq.dispatchers',
                'class_name': 'EmailDispatcher',
                'config_details': {'template_dirs': [str(tmp_path)]}
            }
        }))

        handler.handle(data_object_factory(
            'output_message',
            id_='n1',
            attributes={
                'message_type': 'notification',
                'context': {
                    'id': 'n1',
                    'channels': ['email'],
                    'type': 'sample_ready',
                    'recipients': [
                        {'email': 'a@example.com'},
                        {'email': 'b@example.com'}
                    ],
                    'context': {'sample': '<b>X1</b>'}
                }
            }
        ))

        messages = [_message(m['ID']) for m in _wait_for_messages(2)]
        assert sorted(m['To'][0]['Address'] for m in messages) == [
            'a@example.com', 'b@example.com'
        ]

        for message in messages:
            address = message['To'][0]['Address']
            assert len(message['To']) == 1
            assert message['Subject'] == 'Sample <b>X1</b> is ready'
            assert f'&lt;b&gt;X1&lt;/b&gt; for {address}' in message['HTML']
            assert 'Wellcome Sanger Institute' in message['HTML']
