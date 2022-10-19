# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .resource import AutoResourceGroup
from .service import BaseService
from .schema import BaseSchema
from .swagger import BaseSwagger


class Auto():
    _auto_generated_apis = []

    @classmethod
    def setup_model_crud(cls, model_class):
        class AutoGenerateSchema(BaseSchema):
            class Meta(BaseSchema.BaseMeta):
                model = model_class

        class AutoGenerateService(BaseService):
            class Meta:
                model = model_class
                schema = AutoGenerateSchema

        class AutoGenerateSwagger(BaseSwagger):
            class Meta:
                schema = AutoGenerateSchema

        class AutoGenerateResourceGroup(AutoResourceGroup):
            class Meta:
                service = AutoGenerateService
                swagger = AutoGenerateSwagger

        AutoGenerateSchema = AutoGenerateSchema.setup()
        AutoGenerateService.setup()
        AutoGenerateSwagger.setup()
        AutoGenerateResourceGroup.setup()
        api = AutoGenerateSwagger.api
        cls._auto_generated_apis.append(api)


def get_auto_generated_apis():
    return Auto._auto_generated_apis
