# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import wraps
from typing import Callable


class BadHTTPMethodException(Exception):
    def __init__(self, method: str):
        super().__init__(
            f'The method "{method}" is invalid for HTTP.'
        )


class ServiceNamespace:
    PERMITTED_METHODS = [
        'get',
        'put',
        'post',
        'delete',
        'patch'
    ]

    def __init__(self):
        self.services = []

    def route(self, path: str):
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

    def doc(self, **doc_kwargs) -> Callable:
        """
        Adds documentation to the decorated method

        Params:
        * doc - the method's documentation
        """
        def decorator(function: Callable) -> Callable:
            self.__check_function_method(function)
            function._doc = doc_kwargs

            @wraps(function)
            def wrapper(*args, **kwargs):
                return function(*args, **kwargs)
            return wrapper
        return decorator

    def __check_function_method(self, function: Callable) -> None:
        method = function.__name__
        if method not in self.PERMITTED_METHODS:
            raise BadHTTPMethodException(method)
