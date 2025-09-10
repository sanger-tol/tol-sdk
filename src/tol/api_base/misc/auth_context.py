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
        """Initialize a NotAuthenticatedError with appropriate error details."""
        detail = 'No user has authenticated for this request'

        super().__init__(title='Unauthorized', detail=detail, status_code=401)


class AuthContext:
    """
    The auth context for a specific request, lasting
    only for its duration.

    Used principally to store the ID for the user making
    a request, if authenticated, but can also be used for
    other things.
    """

    def __init__(self) -> None:
        """Initialize an empty AuthContext with no authenticated user."""
        self.__user_id: Optional[str] = None
        self.__roles: list[str] = []
        self.__memberships: list[str] = []

    @property
    def authenticated(self) -> bool:
        """
        `True` if the user has authenticated successfully,
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
        """Set the user ID for this auth context."""
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
        """Set the roles for this auth context."""
        self.__roles = val

    def __assert_authenticated(self) -> None:
        """
        Assert that the user is authenticated.

        Raises:
            NotAuthenticatedError: If the user is not authenticated.
        """
        if not self.authenticated:
            raise NotAuthenticatedError()

    @property
    def memberships(self) -> list[str]:
        """
        A `list[str]` of memberships assigned to this authenticated user.
        """
        self.__assert_authenticated()

        return self.__memberships

    @memberships.setter
    def memberships(self, val: list[str]) -> None:
        """Set the memberships for this auth context."""
        self.__memberships = val


CtxGetter = Callable[[], AuthContext]
"""
A callable that fetches the global `AuthContext` instance
"""


def default_ctx_getter() -> AuthContext:
    """
    Get the default AuthContext instance for the current Flask request.

    Returns:
        AuthContext: The auth context stored in Flask's global context,
                    or a new instance if none exists.
    """
    return flask.g.setdefault('auth_context', default=AuthContext())
