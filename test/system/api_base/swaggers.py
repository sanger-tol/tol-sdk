# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base.swagger.base import BaseSwagger, setup_swagger

from .schemas import ASchema, BSchema, CSchema, DSchema, ESchema, FSchema, \
    GSchema, HSchema, ISchema, JSchema


@setup_swagger
class ASwagger(BaseSwagger):
    class Meta:
        schema = ASchema


@setup_swagger
class BSwagger(BaseSwagger):
    class Meta:
        schema = BSchema


@setup_swagger
class CSwagger(BaseSwagger):
    class Meta:
        schema = CSchema


@setup_swagger
class DSwagger(BaseSwagger):
    class Meta:
        schema = DSchema


@setup_swagger
class ESwagger(BaseSwagger):
    class Meta:
        schema = ESchema


@setup_swagger
class FSwagger(BaseSwagger):
    class Meta:
        schema = FSchema


@setup_swagger
class GSwagger(BaseSwagger):
    class Meta:
        schema = GSchema


@setup_swagger
class HSwagger(BaseSwagger):
    class Meta:
        schema = HSchema


@setup_swagger
class ISwagger(BaseSwagger):
    class Meta:
        schema = ISchema


@setup_swagger
class JSwagger(BaseSwagger):
    class Meta:
        schema = JSchema
