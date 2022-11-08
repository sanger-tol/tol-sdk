# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..model import Role
from ..schema import RoleSchema

from .base import BaseService, setup_service


@setup_service
class RoleService(BaseService):
    class Meta:
        model = Role
        schema = RoleSchema
