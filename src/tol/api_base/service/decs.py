# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import wraps
from typing import Callable

from flask import request


def provide_body_data(function):
    @wraps(function)
    def wrapper(cls, *args, **kwargs):
        data = request.get_json()
        return function(
            cls,
            *args,
            data,
            **kwargs
        )
    return wrapper


def __parse_parameters():
    keys = (
        'page',
        'page_size',
        'filter',
        'sort_by'
    )
    return {
        key: request.args.get(key)
        for key in keys
    }


def provide_parameters(function):
    @wraps(function)
    def wrapper(cls, *args, **kwargs):
        parameters = __parse_parameters()
        return function(
            cls,
            *args,
            parameters,
            **kwargs
        )
    return wrapper


class ServiceNamespace:
    def __init__(self):
        self.services = []

    def route(self, path: str) -> Callable:
        """
        Routes the decorated service class using the
        specified path (prefixed by the type of the Service)

        Params:
        * path - the path in Flask-RestX format
        """
        def wrapper(cls):
            cls._doc = {
                'path': path
            }
            self.services.append(cls)
            return cls
        return wrapper
