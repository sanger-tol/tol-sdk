# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable

from flask_restx import (
    Namespace as FlaskRestxNamespace,
    Resource
)

from ..service.namespace import ServiceConfig, ServiceMethodConfig, ServiceNamespace
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
        resource_name = '' # TODO make a name!!
        new_resource = type(
            resource_name,
            (Resource,),
            {}
        )
        self.route(new_resource)(path)

    def __get_documented_method(
        self,
        method: Callable,
        method_config: ServiceMethodConfig
    ) -> Callable:
        name = method.__name__

