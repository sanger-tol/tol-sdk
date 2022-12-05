# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .base import BaseSwagger, setup_swagger
from ..schema import StateSchema


@setup_swagger
class StateSwagger(BaseSwagger):
    class Meta:
        schema = StateSchema
