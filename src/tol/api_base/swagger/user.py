# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..schema import UserSchema

from .base import BaseSwagger, setup_swagger


@setup_swagger
class UserSwagger(BaseSwagger):
    class Meta:
        schema = UserSchema
