# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import wraps
from typing import Callable, Dict


ServiceHttpMethodsDict = Dict[str, Callable]
NamespaceHttpMethodsDict = Dict[str, ServiceHttpMethodsDict]


class BadHTTPMethodException(Exception):
    def __init__(self, method: str):
        super().__init__(
            f'The method "{method}" is invalid for HTTP. '
            'Please name your methods after a lowercase HTTP method.'
        )


class ServiceNamespace:
    """
    Registers and documents the services for a type.
    """

    __PERMITTED_METHODS = [
        'get',
        'put',
        'post',
        'delete',
        'patch'
    ]

    def __init__(self):
        self.__services: Dict[str, object] = {}

    def route(self, path: str) -> object:
        """
        Routes the decorated service class using the
        specified path (this will automatically beprefixed
        by the type of the Service)

        Params:
        * path - the path in Flask-RestX format
        """
        def wrapper(cls):
            cls._doc = {
                'path': path
            }
            self.__services[path] = cls
            return cls
        return wrapper

    def doc(self, **doc_kwargs) -> Callable:
        """
        Adds documentation to the decorated method

        Params:
        * doc_kwargs    - the method's documentation (in
                          flask-restx format)
        """
        def decorator(function: Callable) -> Callable:
            self.__check_function_method(function)
            function._doc = doc_kwargs

            @wraps(function)
            def wrapper(*args, **kwargs):
                return function(*args, **kwargs)
            return wrapper
        return decorator

    def identify_http_methods(self) -> NamespaceHttpMethodsDict:
        return {
            path: self.__identify_http_methods_on_service(service)
            for path, service in self.__services.items()
        }

    def __service_has_http_method(self, service: object, method: str) -> bool:
        return callable(
            getattr(service, method, None)
        )

    def __identify_http_methods_on_service(self, service: object) -> ServiceHttpMethodsDict:
        return {
            method: getattr(service, method)
            for method in self.__PERMITTED_METHODS
            if self.__service_has_http_method(service, method)
        }

    def __check_function_method(self, function: Callable) -> None:
        method = function.__name__
        if method not in self.__PERMITTED_METHODS:
            raise BadHTTPMethodException(method)
