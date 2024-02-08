# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask import Blueprint, Flask, request

from .abc import AuthManager
from .error import AuthError
from ..misc import CtxGetter, default_ctx_getter


class AuthBlueprint(Blueprint):
    """
    Holds a reference to its `AuthManager` instance.
    """

    def __init__(
        self,
        auth_manager: AuthManager,
        url_prefix: str
    ) -> None:

        self.__manager = auth_manager

        super().__init__(
            'auth',
            __name__,
            url_prefix=url_prefix
        )

        self.__register_auth_endpoints()

    def register_authenticator(
        self,
        app: Flask,
        ctx_getter: CtxGetter = default_ctx_getter,
        header_name: str = 'token'
    ) -> None:

        self.__manager.register(
            app,
            ctx_getter,
            header_name=header_name
        )

    def __register_auth_endpoints(self) -> None:

        @self.get('/login')
        def login():
            return self.__manager.login(), 200

        @self.post('/token')
        def token():
            body: dict[str, str] = request.json

            return self.__manager.get_token_from_callback(
                body['state'],
                body['code']
            ), 200

        @self.post('/profile')
        def profile():
            body: dict[str, str] = request.json

            return self.__manager.create_user_profile(
                body['token']
            ), 200

        @self.post('/logout')
        def logout():
            body: dict[str, str] = request.json

            self.__manager.revoke_token(body['token'])

            return {'success': True}, 200

        @self.errorhandler(AuthError)
        def auth_error(e: AuthError):
            return {
                'errors': e.errors
            }, e.status_code
