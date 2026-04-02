# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..excel import (
    CsvDataSource,
    google_csv_datasource_factory,
)


def google_csv(
    google_csv_id: str,
    object_type: str = 'sheet_row',
    type_mapping: dict | None = None,
    **kwargs,
) -> CsvDataSource:
    return google_csv_datasource_factory(
        google_file_id=google_csv_id,
        object_type=object_type,
        type_mapping=type_mapping,
        **kwargs,
    )
