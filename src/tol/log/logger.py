# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import typing

if typing.TYPE_CHECKING:
    from ..core.operator import Upserter


class Logger:
    """
    Logs access requests using a given `DataSource` instance.

    To prevent infinite recursion, `Logger().log()` must not
    have been previously called on this `DataSource` instance.
    """

    def __init__(self, logging_datasource: Upserter) -> None:
        pass
