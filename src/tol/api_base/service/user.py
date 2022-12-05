# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .base import BaseService, setup_service
from ..model import User
from ..schema import UserSchema


@setup_service
class UserService(BaseService):
    class Meta:
        model = User
        schema = UserSchema
