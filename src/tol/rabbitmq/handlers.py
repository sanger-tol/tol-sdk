# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging
from collections.abc import Callable

from tol.rabbitmq.consumer import Handler
from tol.rabbitmq.schema import (
    MessageEnvelope,
    NotificationChannel,
    NotificationDelivery,
    NotificationRequest,
    create_deliveries
)

LOGGER = logging.getLogger(__name__)

Dispatcher = Callable[[NotificationDelivery], None]


def notification_handler(
    dispatchers: dict[NotificationChannel, Dispatcher]
) -> Handler:
    """
    Build a handler that fans out a notification envelope
    into per-channel deliveries and dispatches each one.

    Register under the 'notification' message type.
    """
    def handle(envelope: MessageEnvelope) -> None:
        request = NotificationRequest.model_validate(envelope.context)
        for delivery in create_deliveries(request):
            dispatcher = dispatchers.get(delivery.channel)
            if dispatcher is None:
                LOGGER.warning(
                    'No dispatcher for channel %s, skipping',
                    delivery.channel
                )
                continue

            dispatcher(delivery)

    return handle
