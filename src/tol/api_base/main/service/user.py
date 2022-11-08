# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..model import User
from ..schema import UserSchema

from .base import BaseService, setup_service


@setup_service
class UserService(BaseService):
    class Meta:
        model = User
        schema = UserSchema
