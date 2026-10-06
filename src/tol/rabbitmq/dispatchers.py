# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from tol.notify import EmailConfig, EmailSender, TemplateRenderer
from tol.rabbitmq.schema import NotificationDelivery


class Dispatcher(ABC):
    """
    Delivers one `NotificationDelivery` on one channel.

    Subclasses declare a nested `Config` dataclass, like handlers.
    Must be idempotent on `delivery_id`.
    """

    @abstractmethod
    def dispatch(self, delivery: NotificationDelivery) -> None:
        """Deliver one notification; raising rejects the whole message."""


class EmailDispatcher(Dispatcher):
    """
    Sends one email per delivery, configured from `SMTP_*`.

    The template name is the notification `type`. Templates see the
    request `context` plus `recipient` (reserved; overrides any context key
    of the same name).
    """

    @dataclass(frozen=True, kw_only=True)
    class Config:
        template_dirs: list[str] = field(default_factory=list)
        """App template directories, searched before the SDK's."""

    def __init__(
        self,
        config: Config,
        sender: EmailSender | None = None,
        renderer: TemplateRenderer | None = None,
        **kwargs: Any
    ) -> None:
        self.__sender = (
            sender if sender is not None
            else EmailSender(EmailConfig.from_env())
        )
        self.__renderer = (
            renderer if renderer is not None
            else TemplateRenderer(config.template_dirs)
        )

    def dispatch(self, delivery: NotificationDelivery) -> None:
        """Render the delivery's template and email its recipient."""
        email = delivery.recipient.email
        if not email:
            raise ValueError(
                f'Delivery {delivery.delivery_id} has no recipient email'
            )

        subject, html = self.__renderer.render(
            delivery.type,
            {**delivery.context, 'recipient': delivery.recipient}
        )
        self.__sender.send([email], subject, html)
