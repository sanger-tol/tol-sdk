# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from flask_restx import (
    Namespace as FlaskRestxNamespace,
    Resource
)

from ..service.namespace import (
    ServiceConfig,
    ServiceMethodConfig,
    ServiceMethodResponse,
    ServiceNamespace
)
from ..swagger.model import Swagger
from ..utils.config import DataTypeConfig


class ApiNamespace(FlaskRestxNamespace):
    """
    Takes a service namespace and implements it using
    flask-restx resources. Consider this a private API!
    """

    def __init__(
        self,
        config: DataTypeConfig,
        custom_service_namespace: ServiceNamespace = None,
        description: str = None
    ) -> None:
        object_type = config.object_type
        super().__init__(
            object_type,
            description=description,
            path=f'/{object_type}'
        )
        self.__initialise_resources(custom_service_namespace)

    def __initialise_resources(self, service_ns: ServiceNamespace) -> None:
        service_dict = service_ns.to_dict()
        for path, service_config in service_dict.items():
            self.__create_resource(path, service_config)

    def __create_resource(
        self,
        path: str,
        service_config: ServiceConfig
    ) -> Resource:
        resource_name = ''  # TODO make a name!!
        methods_dict = self.__get_documented_methods(service_config)
        new_resource = type(
            resource_name,
            (Resource,),
            methods_dict
        )
        self.route(new_resource)(path)

    def __get_documented_methods(
        self,
        service_config: ServiceConfig
    ) -> Dict[str, Callable]:
        service = service_config.service
        return {
            method_name: self.__get_documented_method(
                service,
                method_name,
                method_config
            )
            for method_name, method_config
            in service_config.methods.items()
        }

    def __get_documented_method(
        self,
        service: object,
        method_name: str,
        method_config: ServiceMethodConfig
    ) -> Callable:
        # TODO check self/cls resolves correctly!!!
        # TODO refactor this into smaller chunks

        # get the service method and "clone" it
        method = getattr(service, method_name)

        def decorated(_obj: object, *args, **kwargs) -> Any:
            return method(*args, **kwargs)
        decorated.__name__ = method_name

        decorators = reversed([
            *self.__get_response_decorators(method_config.responses),
            *self.__get_expect_decorator(method_config.expect),
            wraps(decorated)
        ])
        for decorator in decorators:
            decorated = decorator(decorated)
        return decorated

    def __get_expect_decorator(
        self,
        swagger: Optional[Swagger]
    ) -> List[Callable]:
        if swagger is None:
            return []
        else:
            return self.expect(swagger)

    def __get_response_decorators(
        self,
        response_config: Optional[Dict[int, ServiceMethodResponse]]
    ) -> List[Callable]:
        if response_config is None:
            return []
        else:
            return [
                self.__get_response_decorator(status_code, response)
                for status_code, response
                in response_config.items()
            ]

    def __get_response_decorator(
        self,
        status_code: int,
        response: ServiceMethodResponse
    ) -> Callable:
        return self.response(
            status_code,
            response.description,
            model=response.swagger
        )
