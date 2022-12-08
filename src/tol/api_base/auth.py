# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import wraps

from flask import request

from flask_restx import Namespace

from .model import get_user_id_via_token


authorizations = {
    'ApiKeyAuth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Token'
    }
}


def auth_dec():
    def wrap_decorator(function):
        @wraps(function)
        def decorated(resource, *args, **kwargs):
            token = request.headers.get('Token')
            if not token:
                return resource.auth_error('Auth token is missing')
            user_id = get_user_id_via_token(token)
            if user_id is None:
                return resource.auth_error('User does not exist')
            return function(resource, *args, user_id=user_id, **kwargs)
        return decorated
    return wrap_decorator


def auth(namespace: Namespace):
    decs = (
        namespace.response(401, description='Unauthorized'),
        namespace.doc(security=['ApiKeyAuth']),
        auth_dec()
    )

    def deco(func):
        for dec in reversed(decs):
            func = dec(func)
        return func
    return deco
