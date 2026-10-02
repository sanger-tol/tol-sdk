# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.notify import EmailSender, TemplateRenderer
from tol.rabbitmq.handlers import Dispatcher
from tol.rabbitmq.schema import NotificationDelivery


def email_dispatcher(
    sender: EmailSender,
    renderer: TemplateRenderer
) -> Dispatcher:
    """
    Build a dispatcher that sends one email per delivery.

    The template name is the notification `type`. Templates see the
    request `context` plus `recipient` (reserved; overrides any context key
    of the same name).
    """
    def dispatch(delivery: NotificationDelivery) -> None:
        email = delivery.recipient.email
        if not email:
            raise ValueError(
                f'Delivery {delivery.delivery_id} has no recipient email'
            )

        subject, html = renderer.render(
            delivery.type,
            {**delivery.context, 'recipient': delivery.recipient}
        )
        sender.send([email], subject, html)

    return dispatch
