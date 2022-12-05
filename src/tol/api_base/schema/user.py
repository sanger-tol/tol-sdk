# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .base import BaseSchema, setup_schema
from ..model import User


@setup_schema
class UserSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = User
        # exclude access credentials
        exclude = ('api_key', 'token')
