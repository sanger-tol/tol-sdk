# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from jinja2 import TemplateNotFound

import pytest

from tol.notify import EmailSendError, EmailSender, TemplateRenderer
from tol.rabbitmq.dispatchers import email_dispatcher
from tol.rabbitmq.handlers import notification_handler
from tol.rabbitmq.schema import (
    NotificationChannel,
    NotificationDelivery,
    NotificationRequest,
    Recipient,
    wrap_in_envelope
)


def _delivery(**overrides):
    """Build an email NotificationDelivery with optional overrides."""
    fields = {
        'notification_id': 'n1',
        'version': 1,
        'delivery_id': 'n1:email:0',
        'channel': NotificationChannel.EMAIL,
        'recipient': Recipient(email='a@example.com'),
        'type': 'sample_ready',
        'context': {'sample': 'X'}
    }
    fields.update(overrides)
    return NotificationDelivery(**fields)


@pytest.fixture
def sender():
    """An autospecced EmailSender."""
    return create_autospec(EmailSender, instance=True)


@pytest.fixture
def renderer():
    """An autospecced TemplateRenderer returning a fixed email."""
    renderer = create_autospec(TemplateRenderer, instance=True)
    renderer.render.return_value = ('Subject', '<p>Body</p>')
    return renderer


class TestEmailDispatchers:
    def test_renders_type_and_sends_to_recipient(self, sender, renderer):
        """Test that the type picks the template and one email is sent."""
        delivery = _delivery()

        email_dispatcher(sender, renderer)(delivery)

        renderer.render.assert_called_once_with(
            'sample_ready', {'sample': 'X', 'recipient': delivery.recipient}
        )

        sender.send.assert_called_once_with(
            ['a@example.com'], 'Subject', '<p>Body</p>'
        )

    def test_recipient_overrides_context(self, sender, renderer):
        """Test that a publisher cannot spoof the reserved recipient key."""
        delivery = _delivery(context={'recipient': 'spoofed'})

        email_dispatcher(sender, renderer)(delivery)

        context = renderer.render.call_args.args[1]
        assert context['recipient'] == delivery.recipient

    def test_missing_email_raises(self, sender, renderer):
        """Test that a delivery without an email is never sent."""
        delivery = _delivery(recipient=Recipient(user_id='u1'))

        with pytest.raises(ValueError, match='n1:email:0'):
            email_dispatcher(sender, renderer)(delivery)

        sender.send.assert_not_called()

    def test_render_error_sends_nothing(self, sender, renderer):
        """Test that a template failure propagates before any send."""
        renderer.render.side_effect = TemplateNotFound('sample_ready')

        with pytest.raises(TemplateNotFound):
            email_dispatcher(sender, renderer)(_delivery())

        sender.send.assert_not_called()

    def test_send_error_propagates(self, sender, renderer):
        """Test that SMTP failures reach the consumer (and so the DLQ)."""
        sender.send.side_effect = EmailSendError(['a@example.com'], 'sad')

        with pytest.raises(EmailSendError):
            email_dispatcher(sender, renderer)(_delivery())


class TestWithNotificationHandler:
    def test_one_email_per_recipient(self, sender, renderer):
        """Test that each recipient gets their own email."""
        request = NotificationRequest(
            id='n1',
            channels=[NotificationChannel.EMAIL],
            type='sample_ready',
            recipients=[
                Recipient(email='a@example.com'),
                Recipient(email='b@example.com')
            ],
            context={'sample': 'X'}
        )

        handle = notification_handler({
            NotificationChannel.EMAIL: email_dispatcher(sender, renderer)
        })

        handle(wrap_in_envelope(request, source='sdk-test'))

        assert [c.args[0] for c in sender.send.call_args_list] == [
            ['a@example.com'], ['b@example.com']
        ]
