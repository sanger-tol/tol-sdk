# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pathlib
from datetime import datetime

import pytest

from tol.excel import s3_excel_datasource_factory
from tol.excel.s3_factory import S3Fetcher


BASE_DIR = pathlib.Path(__file__).parent.resolve()


@pytest.fixture(scope='module')
def object_type() -> str:
    return 'test_indeed'


@pytest.fixture(scope='module')
def mock_s3_filename() -> str:
    return 'anything'


@pytest.fixture(scope='module')
def mock_s3_bucket() -> str:
    return 'somethign_comforting'


@pytest.fixture(scope='module')
def objects_filename() -> pathlib.Path:
    return BASE_DIR / 'objects.xlsx'


@pytest.fixture
def mock_s3_fetcher(
    mock_s3_filename: str,
    mock_s3_bucket: str,
    objects_filename: pathlib.Path,
) -> S3Fetcher:

    def __mock(
        s3_filename: str,
        s3_bucket: str,
        local_filename: str,
    ) -> None:

        assert s3_filename == mock_s3_filename
        assert s3_bucket == mock_s3_bucket

        with open(local_filename, 'wb') as out_fil:
            with open(objects_filename, 'rb') as in_fil:
                out_fil.write(
                    in_fil.read()
                )

    return __mock


class TestS3Excel:

    def test_get_list(
        self,
        object_type: str,
        mock_s3_filename: str,
        mock_s3_bucket: str,
        mock_s3_fetcher: S3Fetcher,
    ) -> None:
        """Using a real spreadsheet (and mock S3)."""

        emitter = s3_excel_datasource_factory(
            s3_filename=mock_s3_filename,
            s3_bucket=mock_s3_bucket,
            sheetname='Sheet1',
            s3_fetcher=mock_s3_fetcher,
            object_type=object_type,
        )

        obj1, obj2 = list(
            emitter.get_list(object_type)
        )

        assert obj1.type == object_type
        assert obj1.id == '2'  # Row 2
        dt1 = obj1.attributes.pop('datetime_column')
        assert obj1.attributes == {
            'bool_column': True,
            'float_column': 42.0,
            'int_column': 42,
            'str_column': 'hello',
        }
        assert dt1 == datetime(
            year=2000,
            month=2,
            day=18,
        )

        assert obj2.type == object_type
        assert obj2.id == '3'  # Row 3
        dt2 = obj2.attributes.pop('datetime_column')
        assert obj2.attributes == {
            'bool_column': False,
            'float_column': 9032.2,
            'int_column': 9093,
            'str_column': 'world',
        }
        assert dt2 == datetime(
            year=2010,
            month=2,
            day=18,
        )
