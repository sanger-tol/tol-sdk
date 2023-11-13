# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import typing
from typing import Callable, Optional

if typing.TYPE_CHECKING:
    from ..core import DataSource
    from ..core.operator import Upserter


IdGetter = Callable[[], Optional[str]]


class Logger:
    """
    Logs access requests using a given `DataSource` instance
    that implements `Upserter`.

    To prevent infinite recursion, `Logger().log()` must not
    have been previously called on this `DataSource` instance.
    """

    def __init__(
        self,
        logging_datasource: Upserter,
        uuid_generator: Callable[[], str] = None,
        user_id_getter: IdGetter = None
    ) -> None:
        pass

    def log(self, logged: DataSource) -> None:
        """
        Adds logging to the various operation methods
        supported by the `logged` `DataSource` instance.

        For now, just the `user_id` and `datetime` of
        the request.
        """
