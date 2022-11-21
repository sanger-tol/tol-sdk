# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..schema import StateSchema

from .base import BaseSwagger, setup_swagger


@setup_swagger
class StateSwagger(BaseSwagger):
    class Meta:
        schema = StateSchema
