# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pathlib

import pytest

from tol.excel import CsvDataSource, google_csv_datasource_factory


BASE_DIR = pathlib.Path(__file__).parent.resolve()


@pytest.fixture(scope='module')
def object_type() -> str:
    return 'record'


@pytest.fixture(scope='module')
def type_mapping() -> dict[str, str]:
    return {
        'species': 'str',
    }


class TestCsvDataSource:

    def test_get_list(
        self,
        object_type: str,
        type_mapping: dict[str, str],
    ) -> None:
        """Using a real spreadsheet."""
        file_id = '1zTXUUXq7CLgqfbiNaxwi57Fvhzx9bvcX'  # Publicly available test file

        ds = google_csv_datasource_factory(
            google_file_id=file_id,
            object_type=object_type,
            type_mapping=type_mapping,
        )
        assert isinstance(ds, CsvDataSource)

        objs = list(
            ds.get_list(object_type)
        )
        assert objs[0].type == object_type
        assert objs[0].id == '2'
        assert objs[0].attributes['species'] == 'Adetoxenus Formosus'
