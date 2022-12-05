# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .base import BaseService, setup_service
from ..model import State
from ..schema import StateSchema


@setup_service
class StateService(BaseService):
    class Meta:
        model = State
        schema = StateSchema
