# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base.service.base import BaseService, provide_body_data, setup_service

from .models import AModelRelationship, BModelRelationship, CModelWithNullableColumn, \
    DModelWithNonNullableColumn, EModelRelationship, FModelWithExtField, \
    GModelWithFilterableFields, HModelLog, IModelEnum, JModelEnumDependent
from .schemas import ASchema, BSchema, CSchema, DSchema, ESchema, FSchema, \
    GSchema, HSchema, ISchema, JSchema


@setup_service
class AService(BaseService):
    class Meta:
        model = AModelRelationship
        schema = ASchema


@setup_service
class BService(BaseService):
    class Meta:
        model = BModelRelationship
        schema = BSchema


@setup_service
class CService(BaseService):
    class Meta:
        model = CModelWithNullableColumn
        schema = CSchema


@setup_service
class DService(BaseService):
    class Meta:
        model = DModelWithNonNullableColumn
        schema = DSchema


@setup_service
class EService(BaseService):
    class Meta:
        model = EModelRelationship
        schema = ESchema


@setup_service
class FService(BaseService):
    class Meta:
        model = FModelWithExtField
        schema = FSchema


@setup_service
class GService(BaseService):
    class Meta:
        model = GModelWithFilterableFields
        schema = GSchema


@setup_service
class HService(BaseService):
    class Meta:
        model = HModelLog
        schema = HSchema

    @classmethod
    def return_42(cls):
        return {'data': 42}, 200


@setup_service
class IService(BaseService):
    class Meta:
        model = IModelEnum
        schema = ISchema

    @classmethod
    @provide_body_data
    def parrot(cls, body_data, **kwargs):
        return body_data, 200


@setup_service
class JService(BaseService):
    class Meta:
        model = JModelEnumDependent
        schema = JSchema
