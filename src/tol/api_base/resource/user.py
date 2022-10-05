# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..service import UserService
from ..swagger import UserSwagger

from .base import AutoResourceGroup, setup_resource_group


api_user = UserSwagger.api


@setup_resource_group
class UserResourceGroup(AutoResourceGroup):
    class Meta:
        service = UserService
        swagger = UserSwagger
