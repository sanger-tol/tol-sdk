# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable

from tol.rabbitmq.consumer import Handler
from tol.rabbitmq.schema import (
    MessageEnvelope,
    NotificationChannel,
    NotificationDelivery,
    NotificationRequest,
    create_deliveries
)

Dispatcher = Callable[[NotificationDelivery], None]


def notification_handler(
    dispatchers: dict[NotificationChannel, Dispatcher]
) -> Handler:
    """
    Build a handler that fans out a notification envelope
    into per-channel deliveries and dispatches each one.

    Register under the 'notification' message type. Dispatchers must be
    idempotent on `delivery_id`: a redelivery or DLQ replay re-runs every
    delivery, including ones that have already succeeded.
    """
    def handle(envelope: MessageEnvelope) -> None:
        request = NotificationRequest.model_validate(envelope.context)

        missing = set(request.channels) - dispatchers.keys()
        if missing:
            raise LookupError(
                f'No dispatcher for channel(s): {", ".join(sorted(missing))}'
            )

        for delivery in create_deliveries(request):
            dispatchers[delivery.channel](delivery)

    return handle
