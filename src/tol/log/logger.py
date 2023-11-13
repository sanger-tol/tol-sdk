# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from datetime import datetime
from functools import wraps
from typing import Callable, Optional
from uuid import uuid4

from ..core.operator import Deleter, Updater, Upserter

if typing.TYPE_CHECKING:
    from ..core import DataSource


class Logger:
    """
    Logs access requests using a given `DataSource` instance
    that implements `Upserter`.

    To prevent infinite recursion, `Logger().register()` must not
    have been previously called on this `DataSource` instance.
    """

    __METHOD_OPERATOR_MAPPING = {
        'delete': Deleter,
        'update': Updater,
        'upsert': Upserter
    }

    def __init__(
        self,
        logging_datasource: Upserter,
        app_name: str,
        user_id_getter: Callable[[], Optional[str]],
        datetime_now: Callable[[], str] = lambda: str(datetime.now()),
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

        for name, operator in self.__METHOD_OPERATOR_MAPPING.keys():
            if isinstance(logged, operator):
                self.__decorate_operation(logged, name)

    def __decorate_operation(
        self,
        logged: DataSource,
        operation: str
    ) -> None:

        method = getattr(logged, operation)

        def decorator(func: Callable):

            @wraps(func)
            def wrapper(obj, object_type, *args, **kwargs):
                return func(obj, object_type, *args, **kwargs)

            return wrapper

        setattr(logged, operation, decorator(method))
