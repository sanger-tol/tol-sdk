# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from jinja2 import TemplateNotFound

import pytest

from tol.notify import EmailSendError, EmailSender, TemplateRenderer
from tol.rabbitmq.dispatchers import EmailDispatcher
from tol.rabbitmq.schema import (
    NotificationChannel,
    NotificationDelivery,
    Recipient
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


def _dispatcher(sender, renderer=None, **config):
    """An EmailDispatcher with an injected sender (and renderer)."""
    return EmailDispatcher(
        EmailDispatcher.Config(**config),
        sender=sender,
        renderer=renderer
    )


class TestEmailDispatcher:
    def test_renders_type_and_sends_to_recipient(self, sender, renderer):
        """Test that the type picks the template and one email is sent."""
        delivery = _delivery()

        _dispatcher(sender, renderer).dispatch(delivery)

        renderer.render.assert_called_once_with(
            'sample_ready', {'sample': 'X', 'recipient': delivery.recipient}
        )
        sender.send.assert_called_once_with(
            ['a@example.com'], 'Subject', '<p>Body</p>'
        )

    def test_recipient_overrides_context(self, sender, renderer):
        """Test that a publisher cannot spoof the reserved recipient key."""
        delivery = _delivery(context={'recipient': 'spoofed'})

        _dispatcher(sender, renderer).dispatch(delivery)

        context = renderer.render.call_args.args[1]
        assert context['recipient'] == delivery.recipient

    def test_missing_email_raises(self, sender, renderer):
        """Test that a delivery without an email is never sent."""
        delivery = _delivery(recipient=Recipient(user_id='u1'))

        with pytest.raises(ValueError, match='n1:email:0'):
            _dispatcher(sender, renderer).dispatch(delivery)

        sender.send.assert_not_called()

    def test_render_error_sends_nothing(self, sender, renderer):
        """Test that a template failure propagates before any send."""
        renderer.render.side_effect = TemplateNotFound('sample_ready')

        with pytest.raises(TemplateNotFound):
            _dispatcher(sender, renderer).dispatch(_delivery())

        sender.send.assert_not_called()

    def test_send_error_propagates(self, sender, renderer):
        """Test that SMTP failures reach the consumer (and so the DLQ)."""
        sender.send.side_effect = EmailSendError(['a@example.com'], 'sad')

        with pytest.raises(EmailSendError):
            _dispatcher(sender, renderer).dispatch(_delivery())

    def test_config_template_dirs_are_searched(self, sender, tmp_path):
        """Without an injected renderer, Config.template_dirs is used."""
        (tmp_path / 'sample_ready.subject.txt').write_text('Sample {{ sample }}')
        (tmp_path / 'sample_ready.body.html').write_text(
            '<p>{{ recipient.email }}</p>'
        )

        _dispatcher(sender, template_dirs=[str(tmp_path)]).dispatch(
            _delivery()
        )

        sender.send.assert_called_once_with(
            ['a@example.com'], 'Sample X', '<p>a@example.com</p>'
        )
