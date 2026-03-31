# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.excel import CsvDataSource
from tol.sources.google_csv import google_csv 


@pytest.fixture(scope='module')
def object_type() -> str:
    return 'record'


@pytest.fixture(scope='module')
def type_mapping() -> dict[str, str]:
    return {
        'ID': 'str',
        'Kingdom': 'str',
    }


class TestGoogleCsvDataSource:

    def test_get_list(
        self,
        object_type: str,
        type_mapping: dict[str, str],
    ) -> None:
        file_id = '1GUNRDgaVtOVDj_1_ubZzDR72UhvUTQhM'

        ds = google_csv(
            google_csv_id=file_id,
            object_type=object_type,
            type_mapping=type_mapping,
        )
        assert isinstance(ds, CsvDataSource)

        objs = list(
            ds.get_list(object_type)
        )
        assert objs[0].type == object_type
        assert objs[0].id == '2'
        assert objs[0].attributes['ID'] == '1'
        assert objs[0].attributes['Kingdom'] == 'Plantae'
