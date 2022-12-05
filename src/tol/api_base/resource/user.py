# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .base import AutoResourceGroup, setup_resource_group
from ..service import UserService
from ..swagger import UserSwagger


api_user = UserSwagger.api


@setup_resource_group
class UserResourceGroup(AutoResourceGroup):
    class Meta:
        service = UserService
        swagger = UserSwagger
