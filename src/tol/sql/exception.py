# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

from ..core import DataSourceError

if typing.TYPE_CHECKING:
    from .model import Model


class BadColumnError(DataSourceError):
    def __init__(self, model: Model, column_name: str):
        detail = (
            f'The column with name "{column_name}" does not exist '
            f'on the model with tablename "{model.get_table_name()}".'
        )
        super().__init__('Bad Column', detail, 400)
