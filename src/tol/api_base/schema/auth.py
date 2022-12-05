# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .base import BaseSchema, setup_schema
from ..model import Auth


@setup_schema
class AuthSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = Auth
