# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional, Union
from uuid import uuid4

from ..core import DataObject, DataSource
from ..core.operator import Deleter, Updater, Upserter


LoggingDataSource = Union[DataSource, Upserter]
UserIdGetter = Callable[[], Optional[str]]


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
        logging_datasource: LoggingDataSource,
        app_name: str,
        user_id_getter: UserIdGetter,
        datetime_now: Callable[[], str] = lambda: str(datetime.now()),
        uuid_generator: Callable[[], str] = lambda: uuid4().hex
    ) -> None:

        self.__logging_ds = logging_datasource
        self.__log_object_type = f'log-{app_name}'
        self.__user_id_getter = user_id_getter
        self.__datetime_now = datetime_now
        self.__uuid_generator = uuid_generator

    def register(self, logged: DataSource) -> None:
        """
        Adds logging to the various operation methods
        supported by the `logged` `DataSource` instance.

        For now, just the `user_id` and `datetime` of
        the request.
        """

        for name, operator in self.__METHOD_OPERATOR_MAPPING.items():
            if isinstance(logged, operator):
                self.__decorate_operation(logged, name)

    def __log_operation(self, object_type: str, operation: str) -> None:
        log_object = self.__create_log_object(object_type, operation)
        try:
            self.__logging_ds.upsert(
                self.__log_object_type,
                [log_object]
            )
        except Exception as e:
            print(f'Unknown logging error: {e}')

    def __create_log_object(self, object_type: str, operation: str) -> DataObject:
        log_data = {
            'user_id': self.__user_id_getter(),
            '_object_type': object_type,
            'operation': operation,
            'datetime': self.__datetime_now()
        }
        return self.__logging_ds.data_object_factory(
            self.__log_object_type,
            id_=self.__uuid_generator(),
            data=log_data
        )

    def __decorate_operation(
        self,
        logged: DataSource,
        operation: str
    ) -> None:

        method = getattr(logged, operation)

        def decorator(func: Callable):

            def wrapper(object_type, *args, **kwargs):
                return_val = func(object_type, *args, **kwargs)
                if self.__user_id_getter() is not None:
                    self.__log_operation(object_type, operation)
                return return_val

            return wrapper

        setattr(logged, operation, decorator(method))
