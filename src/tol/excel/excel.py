# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import io
from typing import Iterable

import numpy as np

import pandas as pd

from tol.core import DataObject, OperableDataSource


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


def convert_data_objects_to_excel(
    host: OperableDataSource,
    object_type: str,
    data_objects: Iterable[DataObject],
    body: list[dict[str, str]],
    sheet_name: str
):
    # Create a binary stream to where Excel data will be written to
    output_stream = io.BytesIO()
    writer = pd.ExcelWriter(output_stream, engine='xlsxwriter')

    # Extract the visible columns and their order for the excel column headers
    column_order = [field['display_name'] for field in body if not field['hidden']]
    df = pd.DataFrame(columns=column_order)

    for data_object in data_objects:
        data = {}

        for field in body:
            if not field['hidden']:
                display_name = field['display_name']
                key = field['key']
                data[display_name] = data_object.get_field_by_name(key)

        # Append to data frame
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)

    keys = [field['key'] for field in body if not field['hidden']]

    # remove tz info from datetime columns
    dt_keys = __get_datetime_keys(host, object_type, keys)
    both = dict(zip(keys, column_order))
    dt_columns = [both[k] for k in dt_keys]
    df = __make_tz_unaware(df, dt_columns)

    # Convert the data frame to Excel
    df.to_excel(excel_writer=writer, index=False, sheet_name=sheet_name)
    writer.close()

    return output_stream
