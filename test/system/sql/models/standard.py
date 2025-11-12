# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.sql.standard import create_standard_models

from .base import BaseModel


standard_models = create_standard_models(BaseModel)
standard_user_mixin = standard_models._user_mixin
