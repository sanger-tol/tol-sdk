# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .base import BaseSchema, setup_schema
from ..model import State


@setup_schema
class StateSchema(BaseSchema):
    class Meta(BaseSchema.BaseMeta):
        model = State
