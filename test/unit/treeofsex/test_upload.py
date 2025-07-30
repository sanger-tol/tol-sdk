# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from unittest.mock import create_autospec

import pytest

from tol.converter import YamlConverter
from tol.core import OperableDataSource
from tol.excel import ExcelDataSource


@pytest.fixture(scope='class')
def base_dir() -> Path:
    return Path(__file__).resolve().parent.resolve()


@pytest.fixture(scope='class')
def xlsx_filename(base_dir: Path) -> str:
    xlsx_path = base_dir / 'tos_test_upload.xlsx'

    return str(xlsx_path)


@pytest.fixture(scope='class')
def yaml_filename(base_dir: Path) -> str:
    yaml_path = base_dir / 'tos.yaml'

    return str(yaml_path)


@pytest.fixture
def mock_ds() -> OperableDataSource:
    ds: OperableDataSource = create_autospec(
        OperableDataSource,
        spec_set=True,
    )

    ds.supported_types = ['test']

    return ds


class TestTOSUpload:

    def test_upload(
        self,
        xlsx_filename: str,
        yaml_filename: str,
        mock_ds: OperableDataSource,
    ) -> None:

        excel_ds = ExcelDataSource(
            xlsx_filename,
            'attribute',
            object_type='test',
        )

        converter = YamlConverter(
            excel_ds.data_object_factory,
            yaml_filename,
        )

        objects = excel_ds.get_list(
            'test',
        )
        converted = list(
            converter.convert_iterable(objects)
        )

        assert len(converted) == 4

        for obj in objects:
            needed_keys = [
                'source',
                'taxon_id_lol',
                'attribute_key',
                'attribute_value',
                'attribute_state_yeaahhhhhh',
            ]

            for k in needed_keys:
                assert getattr(obj, k)

        first = converted[0]

        assert first.type == 'test'
        assert int(first.id) == 1

        assert first.source == 'book1'
        assert int(first.taxon_id_lol) == 9606
        assert first.attribute_key == 'average_height'
        assert float(first.attribute_value) == 1.8
        assert first.attribute_state_yeaahhhhhh == 'good'
