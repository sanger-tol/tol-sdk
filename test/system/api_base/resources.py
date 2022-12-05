# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import absolute_import

from tol.api_base.auth import auth
from tol.api_base.resource.base import AutoResourceGroup, BaseResource, setup_resource_group

from .services import AService, BService, CService, DService, EService, FService, GService, \
    HService, IService, JService
from .swaggers import ASwagger, BSwagger, CSwagger, DSwagger, ESwagger, FSwagger, GSwagger, \
    HSwagger, ISwagger, JSwagger

api_a = ASwagger.api
api_b = BSwagger.api
api_c = CSwagger.api
api_d = DSwagger.api
api_e = ESwagger.api
api_f = FSwagger.api
api_g = GSwagger.api
api_h = HSwagger.api
api_i = ISwagger.api
api_j = JSwagger.api


@setup_resource_group
class AResource(AutoResourceGroup):
    class Meta:
        service = AService
        swagger = ASwagger


@setup_resource_group
class BResource(AutoResourceGroup):
    class Meta:
        service = BService
        swagger = BSwagger


@setup_resource_group
class CResource(AutoResourceGroup):
    class Meta:
        service = CService
        swagger = CSwagger


@setup_resource_group
class DResource(AutoResourceGroup):
    class Meta:
        service = DService
        swagger = DSwagger


@setup_resource_group
class EResource(AutoResourceGroup):
    class Meta:
        service = EService
        swagger = ESwagger


@setup_resource_group
class FResource(AutoResourceGroup):
    class Meta:
        service = FService
        swagger = FSwagger


@setup_resource_group
class GResource(AutoResourceGroup):
    class Meta:
        service = GService
        swagger = GSwagger


@setup_resource_group
class HResource(AutoResourceGroup):
    class Meta:
        service = HService
        swagger = HSwagger

    @api_h.route('/42')
    class H42Resource(BaseResource):
        @classmethod
        def get(cls):
            return HService.return_42()


@setup_resource_group
class IResource(AutoResourceGroup):
    class Meta:
        service = IService
        swagger = ISwagger

    @api_i.route('/parrot')
    class IParrotResouce(BaseResource):
        @classmethod
        @auth(api_i)
        def post(cls, user_id=None):
            return IService.parrot(user_id=user_id)


@setup_resource_group
class JResource(AutoResourceGroup):
    class Meta:
        service = JService
        swagger = JSwagger
