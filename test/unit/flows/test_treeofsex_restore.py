# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

import pytest

from tol.elastic import ElasticDataSource
from tol.flows.misc import TreeOfSexRestorer
from tol.sql import SqlDataSource


@pytest.fixture
def mock_sql_ds() -> SqlDataSource:
    ds = create_autospec(
        SqlDataSource,
        spec_set=True,
    )

    return ds


@pytest.fixture
def mock_elastic_ds() -> ElasticDataSource:
    ds = create_autospec(
        ElasticDataSource,
        spec_set=True,
    )

    return ds


@pytest.fixture
def mock_cache() -> dict[str, list[str]]:
    return {}


class TestTreeOfSexRestorer:

    def test_restore(
        self,
        mock_sql_ds: SqlDataSource,
        mock_elastic_ds: ElasticDataSource,    
    ) -> None:
        pass

    def test_restore__cache_override(
        self,
        mock_sql_ds: SqlDataSource,
        mock_elastic_ds: ElasticDataSource,
        mock_cache: dict[str, list[str]],
    ) -> None:
        pass
