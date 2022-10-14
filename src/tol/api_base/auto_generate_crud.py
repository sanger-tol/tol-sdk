# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .model import setup_model
from .resource import AutoResourceGroup, setup_resource_group
from .service import BaseService, setup_service
from .schema import BaseSchema, setup_schema
from .swagger import BaseSwagger, setup_swagger


_auto_generated_objects = []


def get_auto_generated_apis():
    return _auto_generated_objects


def auto_generate_crud(cls):
    setup_model(cls)

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
    _auto_generated_objects.append(api)
