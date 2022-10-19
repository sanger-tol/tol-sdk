# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .resource import AutoResourceGroup, setup_resource_group
from .service import BaseService, setup_service
from .schema import BaseSchema, setup_schema
from .swagger import BaseSwagger, setup_swagger


def setup_endpoints(cls):
    cls.setup()
    return cls


class Auto():
    _auto_generated_apis = []

    @classmethod
    def setup(cls):
        cls.setup_model()

        @setup_schema
        class AutoGenerateSchema(BaseSchema):
            class Meta(BaseSchema.BaseMeta):
                model = cls

        @setup_service
        class AutoGenerateService(BaseService):
            class Meta:
                model = cls
                schema = AutoGenerateSchema

        @setup_swagger
        class AutoGenerateSwagger(BaseSwagger):
            class Meta:
                schema = AutoGenerateSchema

        @setup_resource_group
        class AutoGenerateResourceGroup(AutoResourceGroup):
            class Meta:
                service = AutoGenerateService
                swagger = AutoGenerateSwagger

        api = AutoGenerateSwagger.api
        cls._auto_generated_apis.append(api)


def get_auto_generated_apis():
    return Auto._auto_generated_apis
