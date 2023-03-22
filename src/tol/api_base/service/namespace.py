# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..swagger.model import Swagger


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


@dataclass
class ServiceMethodResponse:
    description: Optional[str] = None
    swagger: Optional[Swagger] = None


@dataclass
class ServiceMethodConfig:
    expects: Optional[Swagger] = None
    responses: Optional[Dict[int, ServiceMethodResponse]] = None


@dataclass
class ServiceConfig:
    service: object
    methods: Dict[str, ServiceMethodConfig]


NamespaceServicesConfig = Dict[str, ServiceConfig]


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

    def response(
        self,
        status_code: int,
        description: str = None,
        swagger: Swagger = None
    ) -> Callable:
        """
        Documents a method response.

        Params:
        * status_code   - the status code of this response (e.g. 200)
        * description   - a (short) description of this response
                          (e.g. OK)
        * swagger       - the Swagger model that will be returned
        """

        def decorator(method: Callable) -> Callable:
            self.__validate_function_method(method)
            method._doc['responses'][status_code] = ServiceMethodResponse(
                description=description,
                swagger=swagger
            )

            @wraps(method)
            def wrapper(*args, **kwargs):
                return method(*args, **kwargs)
            return wrapper
        return decorator

    def expects(
        self,
        swagger: Swagger
    ) -> Callable:
        """
        Documents a method with an expected Swagger model on the
        request

        Params:
        * swagger - the Swagger model to expect
        """

        def decorator(method: Callable) -> Callable:
            self.__validate_function_method(method)
            method._doc['expects'] = swagger

            @wraps(method)
            def wrapper(*args, **kwargs):
                return method(*args, **kwargs)
            return wrapper
        return decorator

    def to_dict(self) -> NamespaceServicesConfig:
        """
        Gets the method configuration of all registered services
        """
        return {
            path: self.__get_service_config(service)
            for path, service in self.__services.items()
        }

    def __create_method_doc_if_null(self, method) -> None:
        if not hasattr(method, '_doc'):
            method._doc = {
                'responses': {}
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

    def __get_service_config(self, service: object) -> ServiceConfig:
        return ServiceConfig(
            service=service,
            methods=self.__identify_http_methods_on_service(
                service
            )
        )

    def __validate_function_method(self, method: Callable) -> None:
        name = method.__name__
        if name not in self.__PERMITTED_METHODS:
            raise BadHTTPMethodException(name)
        self.__create_method_doc_if_null(method)

    def __check_service_methods(self, service: object) -> None:
        methods = self.__identify_http_methods_on_service(service)
        if not methods:
            raise NoHTTPMethodsException(service)
