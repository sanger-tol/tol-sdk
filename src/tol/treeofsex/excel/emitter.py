# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from typing import Iterable

import pandas as pd

from ...core import DataObject


class TOSEmitter:
    """
    Emits `DataObject` instances from a tabular
    spreadsheet (e.g. `.xlsx`).
    """

    def __init__(
        self,
        sheet_path: str | Path,
        *,
        object_type: str = 'sheet_row',
        engine: str = 'openpyxl',
    ) -> None:

        pass

    def emit(self) -> Iterable[DataObject]:
        pass
