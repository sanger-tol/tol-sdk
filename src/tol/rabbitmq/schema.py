# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from enum import StrEnum

from nanoid import generate

from pydantic import BaseModel, Field


def generate_unique_id() -> str:
    """Generate a unique ID using nanoid."""
    return generate()


class NotificationChannel(StrEnum):
    EMAIL = 'email'
    SLACK = 'slack'


class Recipient(BaseModel):
    user_id: str | None = None
    email: str | None = None


class RecipientDict(BaseModel):
    user_id: str | None = None
    email: str | None = None


class NotificationRequest(BaseModel):
    id: str  # noqa A003
    version: int = 1
    channels: list[NotificationChannel] = Field(min_length=1)
    type: str  # noqa A003
    recipients: list[Recipient] = Field(min_length=1)
    context: dict[str, object]


class NotificationDelivery(BaseModel):
    notification_id: str
    version: int
    delivery_id: str
    channel: NotificationChannel
    recipient: RecipientDict
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
            recipient=RecipientDict(
                user_id=recipient.user_id,
                email=recipient.email
            ),
            type=notification_request.type,
            context=notification_request.context,
        )
        for channel in notification_request.channels
        for recipient in notification_request.recipients
    ]
