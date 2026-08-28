# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..core import DataObject


class NotificationMessageObject(DataObject):
    """A message on the notification queue. Used only for type hints"""
    body: dict
    routing_key: str | None
    headers: dict | None
    redelivered: bool | None
