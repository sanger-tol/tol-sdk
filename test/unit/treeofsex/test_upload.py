# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest


@pytest.fixture(scope='class')
def base_dir() -> Path:
    return Path.resolve(__file__).parent.resolve()


@pytest.fixture(scope='class')
def xlsx_filename(base_dir: Path) -> str:
    xlsx_path = base_dir / 'test_upload.py'

    return str(xlsx_path)


class TestTOSUpload:

    def test_upload(
        self,
        xlsx_filename: str
    ) -> None:
        """"""
