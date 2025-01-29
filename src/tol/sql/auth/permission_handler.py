# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from functools import wraps
from typing import Callable

from flask import abort
from flask.ext.principal import Permission

from .needs_factory import NeedsFactory
from ...core import DataSourceFilter


class DefaultPermission(Permission):
    def __init__(self, needs: list):
        super(DefaultPermission, self).__init__(needs)


class PermissionManager(ABC):

    @abstractmethod
    def check_permission(
        self,
        object_type: str,
        method: str
    ) -> None:
        pass

    @abstractmethod
    @property
    def filter(
        self
    ) -> DataSourceFilter | None:
        pass


class DefaultPermissionManager(PermissionManager):

    def __init__(
        self,
        object_type: str,
        method: str
    ):

        self.__object_type = object_type
        self.__method = method
        self.__needs = []

        self.__build_needs()

    @property
    def filter(
        self
    ) -> DataSourceFilter | None:
        pass

    @property
    def needs(self) -> list:
        return self.__needs

    # TODO remove!
    def check(
        self,
        method_func: Callable
    ) -> Callable:

        method = method_func.__name__

        @wraps(method_func)
        def _wrapper(*, object_type: str, **kwargs):
            self.check_permission(
                object_type,
                method
            )
            return method_func(
                object_type=object_type,
                **kwargs
            )

        return _wrapper

    def check_permission(
        self,
        object_type: str,
        method: str
    ) -> None:

        permission = DefaultPermission(self.needs)

        if not permission.can():
            abort(403)

    def __build_needs(self) -> None:
        need = NeedsFactory(
            self.__object_type
        ).build_need(self.__method)
        self.__needs.append(need)
