# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .base import BaseSwagger, setup_swagger
from ..schema import UserSchema


@setup_swagger
class UserSwagger(BaseSwagger):
    class Meta:
        schema = UserSchema
