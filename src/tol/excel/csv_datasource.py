# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from typing import Any

import numpy as np

import pandas as pd

from .pandas_datasource import PandasDataSource


class CsvDataSource(
    PandasDataSource
):
    """
    Emits `DataObject` instances from a tabular
    spreadsheet (e.g. `.xlsx`).
    """

    def __init__(
        self,
        filepath: str | Path,
        *,
        object_type: str = 'sheet_row',
        type_mapping: dict[str, str] | None = None,
    ) -> None:

        super().__init__(
            filepath,
            sheet_name=None,
            object_type=object_type,
            type_mapping=type_mapping,
        )

    def _get_dataframe(
        self,
        filepath: str | Path,
        *args: Any
    ) -> pd.DataFrame:

        __df: pd.DataFrame = pd.read_csv(
            filepath
        )

        return __df.replace(np.nan, None)
