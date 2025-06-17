# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from functools import cached_property, reduce, wraps
from typing import Any, Callable

from .datasource_error import DataSourceError
from .operator import (
    ALL_OPERATORS,
    get_operator_member_names,
)

if typing.TYPE_CHECKING:
    from .datasource import OperableDataSource


class DataSourceSession:
    """
    A session for a `DataSource` instance.

    Supports all operations that its `__host` does.
    """

    def __init__(
        self,
        data_source: OperableDataSource
    ) -> None:

        self.__host = data_source

    def __getattribute__(self, __name: str) -> Any:
        if __name.startswith('_'):
            return object.__getattribute__(self, __name)
        else:
            return self.__proxy(__name)

    def __enter__(self) -> OperableSession:
        return self

    def __exit__(self, type_, value, tb) -> None:
        pass

    def __proxy(
        self,
        __name: str
    ) -> Any:
        """Proxies non-local names to `.__host`"""

        self.__validate_proxy(__name)

        proxied = getattr(
            self.__host,
            __name
        )

        if __name not in self.__all_operator_method_dict:
            return proxied

        if not callable(proxied):
            return proxied

        return self.__decorate_add_kwarg(proxied)

    def __decorate_add_kwarg(
        self,
        operator_method: Callable
    ) -> Callable:
        """
        Inserts this instance as the `session` kwarg to the
        given `Callable`'s invocation.
        """

        @wraps(operator_method)
        def wrapper(*args, **kwargs) -> Any:
            return operator_method(
                *args,
                **kwargs,
                session=self
            )

        return wrapper

    def __validate_proxy(self, __name: str) -> None:
        """
        Confirms that the member is implemented
        if it belongs to an `Operator`.
        """

        if __name in self.__all_operator_method_dict:
            operator_name = self.__all_operator_method_dict[__name]

            if operator_name not in self.__operator_names:
                raise DataSourceError(
                    title='Unsupported Operation',
                    detail=(
                        'This Operator method is not implemented '
                        'by the hosting DataSource.'
                    ),
                    status_code=500,
                )

    @cached_property
    def __operator_names(self) -> list[str]:
        """
        A `list` of classnames of implemented operators
        """

        return [
            o.__name__ for o in ALL_OPERATORS
            if isinstance(
                self.__host,
                o
            )
        ]

    @cached_property
    def __all_operator_method_dict(
        self
    ) -> dict[str, str]:
        """
        Maps operation method names to their
        `Operator` name (all, not just
        those implemented)
        """

        inverted = (
            (
                o.__name__,
                get_operator_member_names(o),
            )
            for o in ALL_OPERATORS
        )

        def __act(
            d: dict[str, str],
            o: str,
            names: list[str]
        ) -> dict[str, str]:

            add_dict = {
                n: o for n in names
            }
            return d | add_dict

        return reduce(
            lambda d, p: __act(d, *p),
            inverted,
            {}
        )


if typing.TYPE_CHECKING:

    class OperableSession(
        OperableDataSource,
        DataSourceSession,
    ):
        """A type hint. For inheriting, use `DataSourceSession`."""
