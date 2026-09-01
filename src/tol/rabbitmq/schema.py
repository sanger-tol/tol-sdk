# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from enum import StrEnum

from nanoid import generate

from pydantic import BaseModel, Field, model_validator


def generate_unique_id() -> str:
    """Generate a unique ID using nanoid."""
    return generate()


class NotificationChannel(StrEnum):
    EMAIL = 'email'
    SLACK = 'slack'


class Recipient(BaseModel):
    user_id: str | None = None
    email: str | None = None


class MessageEnvelope(BaseModel):
    """
    Every message on the bus. The consumer routes by `type`;
    each handler owns the meaning of `context`.
    """
    id: str  # noqa A003
    version: int = 1
    type: str  # noqa A003
    context: dict[str, object]


class NotificationRequest(BaseModel):
    id: str  # noqa A003
    version: int = 1
    channels: list[NotificationChannel] = Field(min_length=1)
    type: str  # noqa A003
    recipients: list[Recipient] = Field(min_length=1)
    context: dict[str, object]

    @model_validator(mode='after')
    def _email_channel_requires_emails(self) -> 'NotificationRequest':
        """
        Becasue no central user service exists yet, publishers need emails
        in the context when using the email channel, otherwise they won't get
        delivered.
        """
        if NotificationChannel.EMAIL in self.channels:
            missing = [r for r in self.recipients if not r.email]
            if missing:
                raise ValueError(
                    'email channel requires every recipient to have an email'
                )

        return self


class NotificationDelivery(BaseModel):
    notification_id: str
    version: int
    delivery_id: str
    channel: NotificationChannel
    recipient: Recipient
    type: str  # noqa A003
    context: dict[str, object]


def create_deliveries(notification_request: NotificationRequest
                      ) -> list[NotificationDelivery]:
    """
    Create a list of `NotificationDelivery`
    instances for the given `NotificationRequest`.
    """
    return [
        NotificationDelivery(
            notification_id=notification_request.id,
            version=notification_request.version,
            delivery_id=generate_unique_id(),
            channel=channel,
            recipient=Recipient(
                user_id=recipient.user_id,
                email=recipient.email
            ),
            type=notification_request.type,
            context=notification_request.context,
        )
        for channel in notification_request.channels
        for recipient in notification_request.recipients
    ]


def wrap_in_envelope(request: NotificationRequest) -> dict:
    """
    Serialise a NotificationRequest as an envelope payload for publishing
    """
    return {
        'id': request.id,
        'version': request.version,
        'type': 'notification',
        'context': request.model_dump(mode='json')
    }
