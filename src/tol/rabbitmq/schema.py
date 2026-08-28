# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from enum import StrEnum
from nanoid import generate
from pydantic import BaseModel, Field


def generate_unique_id() -> str:
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
    id: str
    version: int = 1
    channels: list[NotificationChannel] = Field(min_length=1)
    type: str
    recipients: list[Recipient] = Field(min_length=1)
    context: dict[str, object]


class NotificationDelivery(BaseModel):
    notification_id: str
    version: int
    delivery_id: str
    channel: NotificationChannel
    recipient: RecipientDict
    type: str
    context: dict[str, object]


def create_deliveries(notification_request: NotificationRequest) -> list[NotificationDelivery]:
    return [
        NotificationDelivery(
            notification_id=notification_request.id,
            version=notification_request.version,
            delivery_id=generate_unique_id(),
            channel=channel,
            recipient=RecipientDict(user_id=request.user_id, email=request.email),
            type=notification_request.type,
            context=notification_request.context,
        )
        for channel in notification_request.channels
        for request in notification_request.recipients
    ]
