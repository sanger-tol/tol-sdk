# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask_restx import Namespace, fields


class AuthSwagger:
    api = Namespace(
        'auth',
        description='Life Science login authentication',
    )

    login_response = api.model('login_response', {
        'loginUrl': fields.String()
    })

    token_request = api.model('token_request', {
        'code': fields.String(),
        'state': fields.String()
    })

    token_response = api.model('token_response', {
        'token': fields.String()
    })

    profile_request = api.model('profile_request', {
        'token': fields.String()
    })

    profile_response = api.model('profile_response', {
        'email': fields.String(example='user@example.com'),
        'name': fields.String(example='user'),
        'organisation': fields.String(example='Sanger'),
        'roles': fields.Nested(api.model('roles', {
            'role': fields.String(example='admin')
        }), as_list=True, required=True)
    })
