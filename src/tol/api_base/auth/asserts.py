# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import wraps
from typing import Any, Callable, Optional, Protocol

from .error import ForbiddenError
from ..misc.auth_context import AuthContext, CtxGetter, default_ctx_getter
from ...core.datasource_filter import AndFilter
from ...core.operator import OperatorMethod


class AuthInspector(Protocol):
    """
    Intercepts requests to `DataSource` instances behind `data_blueprint`.

    Raises a `ForbiddenError` for insufficient permissions.

    Can also return an update to the `DataSourceFilter().and` terms. (e.g. to
    lock down access to a user's objects by their ID).
    """

    # TODO support segementation within `object_type` - e.g. by programme/project

    def __call__(
        self,
        object_type: str,
        method: OperatorMethod
    ) -> Optional[AndFilter]:
        ...


def _assert_auth(
    ctx: AuthContext,
    required_role: Optional[str]
) -> None:

    if required_role is None:
        return

    if required_role not in ctx.roles:
        raise ForbiddenError()


def require_auth(
    arg_: Optional[Callable] = None,
    *,
    role: Optional[str] = None,

    ctx_getter: CtxGetter = default_ctx_getter
) -> Callable:
    """
    A decorator that asserts the user is logged in, and has the
    the given `role` (if specified).

    Can be used with or without parentheses, but these are mandatory
    if a keyword argument is specified.

    `role` must be specified as a keyword argument, if provided.
    """

    def decorator(func: Callable) -> Callable:

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            ctx = ctx_getter()
            _assert_auth(ctx, role)

            return func(*args, **kwargs)

        return wrapper

    if callable(arg_):
        return decorator(arg_)

    return decorator


NO_AUTH = [
    OperatorMethod.COUNT,
    OperatorMethod.DETAIL,
    OperatorMethod.EXPORT,
    OperatorMethod.PAGE,
    OperatorMethod.TO_MANY,
    OperatorMethod.TO_ONE,
    OperatorMethod.CURSOR
]


def basic_auth_inspector(
    basic_role: str = 'basic',

    ctx_getter: CtxGetter = default_ctx_getter
) -> AuthInspector:
    """
    An `AuthInspector` factory, returning an instance
    that ignores `object_type` and:

    - permits unauthenticated access to read-only methods
    - requires the `basic_role` on an authenticated user
      otherwise
    """

    def auth_inspector(
        __object_type: str,
        method: OperatorMethod
    ) -> None:

        if method in NO_AUTH:
            return

        roles = ctx_getter().roles
        if basic_role not in roles:
            raise ForbiddenError()

    return auth_inspector
