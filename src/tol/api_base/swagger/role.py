# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .base import BaseSwagger, setup_swagger
from ..schema import RoleSchema


@setup_swagger
class RoleSwagger(BaseSwagger):
    class Meta:
        schema = RoleSchema
