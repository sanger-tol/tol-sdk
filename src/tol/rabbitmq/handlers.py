# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any

from tol.core import DataObject, Handler
from tol.rabbitmq.dispatchers import Dispatcher
from tol.rabbitmq.schema import (
    NotificationChannel,
    NotificationRequest,
    create_deliveries
)
from tol.rabbitmq.spec import instantiate


class NotificationHandler(Handler):
    """
    Fans a `notification` message out into one delivery per
    (channel, recipient) and dispatches each.

    Dispatchers must be idempotent on `delivery_id`: a redelivery or DLQ
    replay re-runs every delivery, including ones that already succeeded.
    """

    @dataclass(frozen=True, kw_only=True)
    class Config:
        channels: dict[str, dict[str, Any]]
        """Channel name to a `{module, class_name, config_details}` spec."""

    def __init__(self, config: Config, **kwargs: Any) -> None:
        self.__dispatchers: dict[NotificationChannel, Dispatcher] = {
            NotificationChannel(channel): instantiate(spec, Dispatcher)
            for channel, spec in config.channels.items()
        }

    def handle(self, obj: DataObject) -> None:
        """Validate the request, check every channel, then dispatch."""
        request = NotificationRequest.model_validate(obj.context)

        missing = set(request.channels) - self.__dispatchers.keys()
        if missing:
            raise LookupError(
                f'No dispatcher for channel(s): {", ".join(sorted(missing))}'
            )

        for delivery in create_deliveries(request):
            self.__dispatchers[delivery.channel].dispatch(delivery)
