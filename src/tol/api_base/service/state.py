# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..model import State
from ..schema import StateSchema

from .base import BaseService, setup_service


@setup_service
class StateService(BaseService):
    class Meta:
        model = State
        schema = StateSchema
