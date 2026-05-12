# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import numpy as np

import pandas as pd

from .pandas_datasource import PandasDataSource


class ExcelDataSource(
    PandasDataSource
):
    """
    Emits `DataObject` instances from a tabular
    spreadsheet (e.g. `.xlsx`).
    """

    def __init__(
        self,
        filepath: str | Path,
        sheet_name: str,
        *,
        object_type: str = 'sheet_row',
        engine: str = 'openpyxl',
        type_mapping: dict[str, str] | None = None,
    ) -> None:

        super().__init__(
            filepath,
            sheet_name,
            object_type=object_type,
            engine=engine,
            type_mapping=type_mapping,
        )

    def _get_dataframe(
        self,
        filepath: str | Path,
        sheet_name: str,
        engine: str,
    ) -> pd.DataFrame:

        __df: pd.DataFrame = pd.read_excel(
            filepath,
            sheet_name,
            engine=engine,
        )

        return __df.replace(np.nan, None)
