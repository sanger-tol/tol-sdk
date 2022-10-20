# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .resource import AutoResourceGroup
from .service import BaseService
from .schema import BaseSchema
from .swagger import BaseSwagger


class Auto():
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
        return AutoGenerateSwagger.api
