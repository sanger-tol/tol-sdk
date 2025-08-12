# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import numpy as np

import pandas as pd

from tol.core import OperableDataSource


def convert_excel_to_json(file, sheet_name):
    excel_data = pd.read_excel(file, sheet_name=sheet_name)
    excel_data.replace({np.nan: None}, inplace=True)
    return excel_data.to_dict(orient='records')


def convert_excel_to_valid_json_string(file, sheet_name) -> str:
    """Converts all (date)times to strings"""

    excel_data = pd.read_excel(file, sheet_name=sheet_name)
    excel_data.replace({np.nan: None}, inplace=True)
    return excel_data.to_json(orient='records', date_format='iso')


def __key_is_datetime(
    host: OperableDataSource,
    object_type: str,
    key: str
) -> bool:

    if '.' not in key:
        attr_types = host.attribute_types.get(object_type, {})
        field_type = attr_types.get(key)

        return field_type is not None and 'date' in field_type

    relation, tail = key.split('.', maxsplit=1)
    r_config = host.relationship_config[object_type]
    r_type = r_config.to_one[relation]

    return __key_is_datetime(host, r_type, tail)


def __get_datetime_keys(
    host: OperableDataSource,
    object_type: str,
    keys: list[str]
) -> list[str]:
    """
    the list of column names, out of the selected,
    that may contain timezone info
    """

    return [
        f for f in keys
        if __key_is_datetime(
            host,
            object_type,
            f
        )
    ]


def __make_tz_unaware(
    df: pd.DataFrame,
    datetime_columns: list[str]
) -> pd.DataFrame:
    """
    makes all `datetime` values timezone-unaware in
    a pandas `DataFrame`.
    """

    for column in datetime_columns:
        # (copy and) convert every cell to datetime, with NA if failed
        coerced = pd.to_datetime(df[column], errors='coerce', utc=True)
        # get the 'bitmask' of cells that are datetimes
        datetime_mask = coerced.notna()
        # apply `tz_convert` using the bitmask
        df.loc[datetime_mask, column] = coerced[datetime_mask].dt.tz_convert(None)

    return df
