# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask_restx import Namespace


authorizations = {
    'ApiKeyAuth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}


def auth(namespace: Namespace):
    def decorator(function):
        def wrapper(*args, **kwagrs):
            return function(*args, **kwagrs)
        return wrapper
    return decorator
