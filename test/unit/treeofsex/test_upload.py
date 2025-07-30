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
    return Path.resolve(__file__).parent.resolve()


@pytest.fixture(scope='class')
def xlsx_filename(base_dir: Path) -> str:
    xlsx_path = base_dir / 'test_upload.py'

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

        pass
