# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Any

from flask import Flask, request

from ...misc import AuthContext, CtxGetter


class AuthManager(ABC):
    """Manages user profiles and their tokens."""

    @abstractmethod
    def login(self) -> dict[str, str]:
        """The first part of the OIDC handshake."""

    @abstractmethod
    def get_token_from_callback(
        self,
        state: str,
        code: str
    ) -> dict[str, str]:
        """The second part of the OIDC handshake."""

    @abstractmethod
    def create_user_profile(
        self,
        token: str
    ) -> dict[str, Any]:
        """The third part of the OIDC handshake."""

    @abstractmethod
    def revoke_token(
        self,
        token: str
    ) -> None:
        """Deletes the given token."""

    @abstractmethod
    def authenticate(
        self,
        ctx: AuthContext,
        token: str
    ) -> None:
        """
        Sets `str` user_id corresponding to
        the given `token` on the given `ctx`.
        """

    def register(
        self,
        app: Flask,
        ctx_getter: CtxGetter,
        header_name: str = 'token'
    ) -> None:

        @app.before_request
        def __authenticate() -> None:
            if header_name not in request.headers:
                return
            token = request.headers[header_name]

            self.authenticate(
                ctx_getter(),
                token
            )
