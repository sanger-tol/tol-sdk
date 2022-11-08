# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..model import Role

from .base import BaseSchema, setup_schema


@setup_schema
class RoleSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = Role
