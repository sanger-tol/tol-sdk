# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import smtplib
import ssl
from unittest.mock import Mock, create_autospec

import pytest

from tol.notify import EmailConfig, EmailSendError, EmailSender, SmtpSecurity

_REAL_SMTP = smtplib.SMTP


def _config(**overrides):
    """Build an EmailConfig with optional overrides."""
    fields = {
        'host': 'smtp.example.com',
        'from_address': 'noreply@example.com',
        'port': 587,
        'username': 'user',
        'password': 'secret'
    }
    fields.update(overrides)
    return EmailConfig(**fields)


def _stub(monkeypatch, cls_name):
    """Patch smtplib.<cls_name>; returns (factory, instance) mocks."""
    instance = create_autospec(_REAL_SMTP, instance=True)
    instance.__enter__.return_value = instance
    instance.send_message.return_value = {}
    factory = Mock(return_value=instance)
    monkeypatch.setattr(f'tol.notify.sender.smtplib.{cls_name}', factory)
    return factory, instance


@pytest.fixture
def smtp(monkeypatch):
    """Patch smtplib.SMTP."""
    return _stub(monkeypatch, 'SMTP')


@pytest.fixture
def smtp_ssl(monkeypatch):
    """Patch smtplib.SMTP_SSL."""
    return _stub(monkeypatch, 'SMTP_SSL')


def _sent_message(instance):
    """Return the Emailmessage passed to send_message."""
    return instance.send_message.call_args.args[0]


class TestTransport:
    def test_starttls_call_order(self, smtp):
        """Test that STARTTLS happens before login, login before send."""
        factory, instance = smtp

        EmailSender(_config()).send(['a@example.com'], 'Hi', '<p>Hi</p>')

        factory.assert_called_once_with(
            'smtp.example.com', 587, timeout=30
        )

        assert [c[0] for c in instance.mock_calls] == [
            '__enter__', 'starttls', 'login', 'send_message', '__exit__'
        ]

        assert isinstance(
            instance.starttls.call_args.kwargs['context'], ssl.SSLContext
        )

        instance.login.assert_called_once_with('user', 'secret')

    def test_ssl_uses_smtp_ssl(self, smtp, smtp_ssl):
        """Test that implicit TLS uses SMTP_SSL and skips STARTTLS."""
        plain_factory, _ = smtp
        factory, instance = smtp_ssl

        EmailSender(
            _config(security=SmtpSecurity.SSL, port=465)
        ).send(['a@example.com'], 'Hi', '<p>Hi</p>')

        plain_factory.assert_not_called()
        assert factory.call_args.args == ('smtp.example.com', 465)
        assert isinstance(factory.call_args.kwargs['context'], ssl.SSLContext)
        instance.starttls.assert_not_called()
        instance.send_message.assert_called_once()

    def test_plain_without_credentials(self, smtp):
        """Test that 'none' security neither upgrades or logs in."""
        _, instance = smtp

        EmailSender(_config(
            security=SmtpSecurity.NONE,
            port=1025,
            username=None,
            password=None
        )).send(['a@example.com'], 'Hi', '<p>Hi</p>')

        instance.starttls.assert_not_called()
        instance.login.assert_not_called()
        instance.send_message.assert_called_once()


class TestMessage:
    def test_html_only(self, smtp):
        """Test that without a text body a single HTML part is sent."""
        _, instance = smtp

        EmailSender(_config()).send(
            ['a@example.com', 'b@example.com'], 'Subject', '<p>Body</p>'
        )

        message = _sent_message(instance)
        assert message['From'] == 'noreply@example.com'
        assert message['To'] == 'a@example.com, b@example.com'
        assert message['Subject'] == 'Subject'
        assert message.get_content_type() == 'text/html'

    def test_text_and_html_alternative(self, smtp):
        """Test that a text body produces multipart/alternative."""
        _, instance = smtp

        EmailSender(_config()).send(
            ['a@example.com'], 'Subject', '<p>Body</p>', text_body='Body'
        )

        message = _sent_message(instance)
        assert message.get_content_type() == 'multipart/alternative'
        assert [p.get_content_type() for p in message.iter_parts()] == [
            'text/plain', 'text/html'
        ]

    def test_empty_recipient_raises(self, smtp):
        """Test that sending to nobody is a programming error."""
        factory, _ = smtp

        with pytest.raises(ValueError):
            EmailSender(_config()).send([], 'Hi', '<p>Hi</p>')

        factory.assert_not_called()

    def test_newline_in_subject_rejected(self, smtp):
        """Test that header injection via the subject is impossible."""
        with pytest.raises(ValueError):
            EmailSender(_config()).send(
                ['a@example.com'], 'Hi\r\nBcc: evil@example.com', '<p>Hi</p>'
            )


class TestFailures:
    def test_smtp_error_raises_send_error(self, smtp):
        """Test that SMTP failures surface as EmailSendError."""
        _, instance = smtp
        instance.login.side_effect = smtplib.SMTPAuthenticationError(
            535, b'bad credentials'
        )

        with pytest.raises(EmailSendError) as exc_info:
            EmailSender(_config()).send(['a@example.com'], 'Hi', '<p>Hi</p>')

        assert exc_info.value.recipients == ['a@example.com']
        instance.__exit__.assert_called_once()

    def test_connection_error_raises_send_error(self, smtp):
        """Test that connection failures surface as EmailSendError."""
        factory, _ = smtp
        factory.side_effect = ConnectionRefusedError()

        with pytest.raises(EmailSendError):
            EmailSender(_config()).send(['a@example.com'], 'Hi', '<p>Hi</p>')

    def test_partial_refusal_is_logged_not_raised(self, smtp, caplog):
        """Test that partially refused recipients are logged."""
        _, instance = smtp
        instance.send_message.return_value = {
            'b@example.com': (550, b'no such user')
        }

        EmailSender(_config()).send(
            ['a@example.com', 'b@example.com'], 'Hi', '<p>Hi</p>'
        )

        assert 'b@example.com' in caplog.text
