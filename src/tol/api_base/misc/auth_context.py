# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable, Optional

import flask

from ...core import DataSourceError


class NotAuthenticatedError(DataSourceError):
    """
    Raised when attempting to access `AuthContext`
    properties without a successful authentication event.
    """

    def __init__(self) -> None:
        detail = (
            'No user has authenticated for this request'
        )

        super().__init__(
            title='Unauthorized',
            detail=detail,
            status_code=401
        )


class AuthContext:
    """
    The auth context for a specific request, lasting
    only for its duration.

    Used principally to store the ID for the user making
    a request, if authenticated, but can also be used for
    other things.
    """

    def __init__(self) -> None:
        self.__user_id: Optional[str] = None
        self.__roles: list[str] = []

    @property
    def authenticated(self) -> bool:
        """
        `True` if the user has authenticated succesfully,
        perhaps by using a token.
        """

        return self.__user_id is not None

    @property
    def user_id(self) -> str:
        """A `str` that uniquely identifies a user."""

        self.__assert_authenticated()

        return self.__user_id

    @user_id.setter
    def user_id(self, val: str) -> None:
        self.__user_id = val

    @property
    def roles(self) -> list[str]:
        """
        A `list[str]` of names of roles assigned to
        the authenticated user.
        """

        self.__assert_authenticated()

        return self.__roles

    @roles.setter
    def roles(self, val: list[str]) -> None:
        self.__roles = val

    def __assert_authenticated(self) -> None:
        if not self.authenticated:
            raise NotAuthenticatedError()


CtxGetter = Callable[[], AuthContext]
"""
A callable that fetches the global `AuthContext` instance
"""


def default_ctx_getter() -> AuthContext:
    return flask.g.setdefault(
        'auth_context',
        default=AuthContext()
    )
