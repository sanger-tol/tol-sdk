# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.sql.standard import create_board_models

from .base import BaseModel


board_models = create_board_models(BaseModel)
board_user_mixin = board_models._user_mixin
