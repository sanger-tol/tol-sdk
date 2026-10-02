# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging
import smtplib
import ssl
from email.message import EmailMessage

from .config import EmailConfig, SmtpSecurity

LOGGER = logging.getLogger(__name__)


class EmailSendError(Exception):
    """An email could not be sent to any recipients."""

    def __init__(self, recipients: list[str], reason: str) -> None:
        super().__init__(
            f'Failed to send email to {", ".join(recipients)}: {reason}'
        )

        self.recipients = recipients
        self.reason = reason


class EmailSender:
    """Sends one email per call over a fresh SMTP connection."""

    __slots__ = ('__config')

    def __init__(self, config: EmailConfig) -> None:
        self.__config = config

    def send(
        self,
        to: list[str],
        subject: str,
        html_body: str,
        text_body: str | None = None
    ) -> None:
        if not to:
            raise ValueError('At least one recipient is required')

        message = self.__build_message(to, subject, html_body, text_body)
        config = self.__config

        try:
            with self.__connect() as smtp:
                if config.security is SmtpSecurity.STARTTLS:
                    smtp.starttls(context=ssl.create_default_context())
                if config.username is not None and config.password is not None:
                    smtp.login(config.username, config.password)
                refused = smtp.send_message(message)
        except (smtplib.SMTPException, OSError) as e:
            raise EmailSendError(to, repr(e)) from e

        if refused:
            # Raising would redeliver to recipients that were accepted
            LOGGER.warning('Recipient refused: %s', refused)

    def __connect(self) -> smtplib.SMTP:
        config = self.__config
        if config.security is SmtpSecurity.SSL:
            return smtplib.SMTP_SSL(
                config.host,
                config.port,
                timeout=config.timeout,
                context=ssl.create_default_context()
            )
        return smtplib.SMTP(config.host, config.port, timeout=config.timeout)

    def __build_message(
        self,
        to: list[str],
        subject: str,
        html_body: str,
        text_body: str | None
    ) -> EmailMessage:
        message = EmailMessage()
        message['From'] = self.__config.from_address
        message['To'] = ', '.join(to)
        message['Subject'] = subject

        if text_body is None:
            message.set_content(html_body, subtype='html')
        else:
            message.set_content(text_body)
            message.add_alternative(html_body, subtype='html')

        return message
