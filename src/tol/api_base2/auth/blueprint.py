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
        url_prefix: str,
        ctx_getter: CtxGetter = default_ctx_getter
    ) -> None:

        self.__manager = auth_manager
        self.__ctx_getter = ctx_getter

        super().__init__(
            'auth',
            __name__,
            url_prefix=url_prefix
        )

        self.__register_auth_endpoints()

    def register_authenticator(
        self,
        app: Flask,
        header_name: str = 'token'
    ) -> None:

        self.__manager.register(
            app,
            self.__ctx_getter,
            header_name=header_name
        )

    def __register_auth_endpoints(self) -> None:

        @self.get('/login')
        def login():
            return self.__manager.login(), 200

        @self.post('/token')
        def token():
            body: dict[str, str] = request.json

            res = self.__manager.get_token_from_callback(
                body['state'],
                body['code']
            )

            return res, 200

        @self.post('/profile')
        def profile():
            body: dict[str, str] = request.json

            res = self.__manager.create_user_profile(
                body['token']
            )

            return res, 200

        @self.post('/logout')
        @self.delete('/token')
        def logout():
            body: dict[str, str] = request.json

            self.__manager.revoke_token(body['token'])

            return {'success': True}, 200

        @self.get('/roles')
        def roles():
            ctx = self.__ctx_getter()

            return {
                'id': ctx.user_id,
                'roles': ctx.roles
            }, 200

        @self.errorhandler(AuthError)
        def auth_error(e: AuthError):
            return {
                'errors': e.errors
            }, e.status_code
