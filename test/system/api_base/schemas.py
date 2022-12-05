# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import absolute_import

from tol.api_base.schema.base import BaseSchema, setup_schema

from .models import AModelRelationship, BModelRelationship, CModelWithNullableColumn, \
    DModelWithNonNullableColumn, EModelRelationship, FModelWithExtField, \
    GModelWithFilterableFields, HModelLog, IModelEnum, JModelEnumDependent


@setup_schema
class ASchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = AModelRelationship


@setup_schema
class BSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = BModelRelationship


@setup_schema
class CSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = CModelWithNullableColumn


@setup_schema
class DSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = DModelWithNonNullableColumn


@setup_schema
class ESchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = EModelRelationship


@setup_schema
class FSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = FModelWithExtField


@setup_schema
class GSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = GModelWithFilterableFields


@setup_schema
class HSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = HModelLog


@setup_schema
class ISchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = IModelEnum


@setup_schema
class JSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = JModelEnumDependent
