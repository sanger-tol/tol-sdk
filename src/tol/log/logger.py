# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from typing import Callable, Optional
from uuid import uuid4

if typing.TYPE_CHECKING:
    from ..core import DataSource
    from ..core.operator import Upserter


class Logger:
    """
    Logs access requests using a given `DataSource` instance
    that implements `Upserter`.

    To prevent infinite recursion, `Logger().register()` must not
    have been previously called on this `DataSource` instance.
    """

    def __init__(
        self,
        logging_datasource: Upserter,
        user_id_getter: Callable[[], Optional[str]],
        uuid_generator: Callable[[], str] = lambda: uuid4().hex
    ) -> None:
        pass

    def register(self, logged: DataSource) -> None:
        """
        Adds logging to the various operation methods
        supported by the `logged` `DataSource` instance.

        For now, just the `user_id` and `datetime` of
        the request.
        """
