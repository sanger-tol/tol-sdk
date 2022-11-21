# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask_restx import Resource

from ..service import AuthService
from ..swagger import AuthSwagger


api_auth = AuthSwagger.api


class AuthResourceGroup:
    @api_auth.route('/login')
    class LoginResource(Resource):
        @api_auth.doc('Gets the login URL')
        @api_auth.response(
            200,
            description='Success',
            model=AuthSwagger.login_response,
        )
        def get(self):
            return AuthService.login()

    @api_auth.route('/token')
    class TokenResource(Resource):
        @api_auth.doc('Gets the auth token')
        @api_auth.expect(AuthSwagger.token_request)
        @api_auth.response(
            200,
            description='Success',
            model=AuthSwagger.token_response,
        )
        def post(self, **kwargs):
            return AuthService.get_token_from_callback()

    @api_auth.route('/profile')
    class ProfileResource(Resource):
        @api_auth.doc('Gets and creates a user profile')
        @api_auth.expect(AuthSwagger.profile_request)
        @api_auth.response(
            200,
            description='Success',
            model=AuthSwagger.profile_response,
        )
        def post(self, **kwargs):
            return AuthService.create_user_profile()
