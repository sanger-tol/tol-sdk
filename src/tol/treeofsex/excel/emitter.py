# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from typing import Iterable

import pandas as pd

from ...core import DataObject, DataObjectFactory


class TOSEmitter:
    """
    Emits `DataObject` instances from a tabular
    spreadsheet (e.g. `.xlsx`).
    """

    def __init__(
        self,
        data_object_factory: DataObjectFactory,
        sheet_path: str | Path,
        *,
        column_offset: int = 0,
        row_offset: int = 0,
        object_type: str = 'sheet_row',
        engine: str = 'openpyxl',
    ) -> None:

        pass

    def emit(self) -> Iterable[DataObject]:
        pass
