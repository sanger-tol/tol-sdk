# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable, Optional

from flask import request

from .auth_context import AuthContext
from ...api_client.exception import UnauthenticatedError


Authenticator = Callable[[AuthContext, Optional[str]], None]
"""
A `Callable` that should authenticate the user by:

- adding user details, such as `user_id`, to the
  given request-global `AuthContext`, given a
  `str` token (or `None`)
- raising an `UnauthenticatedError` if invalid
"""


TokenGetter = Callable[[str], Optional[str]]
MethodGetter = Callable[[], str]


def quick_and_dirty_auth(
    omnipotent_token: str,

    omnipotent_user_id: str = '666666',
    token_getter: TokenGetter = lambda h: request.headers.get(h),
    token_header: str = 'token',
    method_getter: MethodGetter = lambda: request.method,
    excluded_methods: list[str] = ['GET']
) -> Authenticator:
    """
    Compares the "token" header to a given
    `omnipotent_value`. There is only one valid token,
    and this is authorised to do everything.

    Override the `excluded_methods` kwarg with a list of
    HTTP methods on which to permit requests without
    checking the user's token. (defaults to just "GET").
    Otherwise, a token is required.

    DO NOT use this function, if it can be avoided!
    """

    def __authenticator(ctx: AuthContext) -> None:
        method = method_getter()
        if method in excluded_methods:
            return

        token = token_getter(token_header)
        if token is None:
            raise UnauthenticatedError(
                'No token was provided'
            )
        if token != omnipotent_token:
            raise UnauthenticatedError(
                'The token provided is invalid.'
            )

        ctx.user_id = omnipotent_user_id

    return __authenticator
