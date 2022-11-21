# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..model import Auth

from .base import BaseSchema, setup_schema


@setup_schema
class AuthSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = Auth
