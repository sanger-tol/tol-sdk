# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .base import BaseSchema, setup_schema
from ..model import Role


@setup_schema
class RoleSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = Role
