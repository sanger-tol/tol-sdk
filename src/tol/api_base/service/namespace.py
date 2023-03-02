# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import wraps
from typing import Any, Callable, Dict, List


ServiceHttpMethodsDict = Dict[str, Any]
NamespaceHttpMethodsDict = Dict[str, ServiceHttpMethodsDict]


class BadHTTPMethodException(Exception):
    def __init__(self, method: str):
        super().__init__(
            f'The method "{method}" is invalid for HTTP. '
            'Please name your methods after a lowercase HTTP method.'
        )


class NoHTTPMethodsException(Exception):
    def __init__(self, service: object):
        super().__init__(
            f'The service class "{service.__name__}" has no HTTP methods.'
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
        specified path (this will automatically be
        prefixed by the type of the Service)

        Params:
        * path - the path in Flask-RestX format
        """
        def wrapper(service):
            self.__check_service_methods(service)
            service._doc = {
                'path': path
            }
            self.__services[path] = service
            return service
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

    def get_services_config(self) -> NamespaceHttpMethodsDict:
        """
        Gets the method configuration of all registered services
        """
        return {
            path: self.__get_service_config(service)
            for path, service in self.__services.items()
        }

    def __service_has_http_method(self, service: object, method: str) -> bool:
        return callable(
            getattr(service, method, None)
        )

    def __identify_http_methods_on_service(self, service: object) -> List[str]:
        return [
            method for method in self.__PERMITTED_METHODS
            if self.__service_has_http_method(service, method)
        ]

    def __get_service_config(self, service: object) -> ServiceHttpMethodsDict:
        return {
            'class': service,
            'methods': self.__identify_http_methods_on_service(
                service
            )
        }

    def __check_function_method(self, function: Callable) -> None:
        method = function.__name__
        if method not in self.__PERMITTED_METHODS:
            raise BadHTTPMethodException(method)

    def __check_service_methods(self, service: object) -> None:
        methods = self.__identify_http_methods_on_service(service)
        if not methods:
            raise NoHTTPMethodsException(service)
