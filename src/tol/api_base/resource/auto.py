# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import List

from flask_restx import (
    Namespace as FlaskRestxNamespace,
    Resource
)

from ..service.namespace import ServiceNamespace
from ..utils.config import IndividualConfig


class ApiNamespace(FlaskRestxNamespace):
    """
    Takes a service namespace and implements it using
    flask-restx resources.
    """

    def __init__(
        self,
        config: IndividualConfig,
        custom_service_ns: ServiceNamespace = None,
        description: str = None
    ) -> None:
        object_type = IndividualConfig.object_type
        self.__config = config
        self.__service_ns = custom_service_ns
        self.__resources: List[Resource] = []
        super(FlaskRestxNamespace, self).__init__(
            object_type,
            description=description,
            path=f'/{object_type}'
        )
        self.__initialise_resources()

    def __initialise_resources(self) -> None:
        pass
