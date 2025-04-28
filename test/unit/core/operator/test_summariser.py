# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

import pytest

from tol.core import DataObject, DataSourceError
from tol.core.operator import Summariser


@pytest.fixture
def mock_summariser() -> Summariser:
    return create_autospec(
        Summariser,
        spec_set=True,
    )


class TestSummariser:

    def test_summarse_all(
        self,
        mock_summariser: Summariser
    ) -> None:
        pass

    def test_summarise_type(
        self,
        mock_summariser: Summariser
    ) -> None:
        pass

    def test_resummarise_by_ids(
        self,
        mock_summariser: Summariser
    ) -> None:
        pass