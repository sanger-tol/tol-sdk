# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter, OperableDataSource

from ..dec import against
from ..fixtures import api_sql, sql


class TestToOneRelatedFiltering:
    """TOLP-8867"""

    @against(api_sql, sql)
    def test_filter_by_to_one_related_id(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ) -> None:

        pass

    @against(api_sql, sql)
    def test_filter_by_to_related_attributes(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ) -> None:

        pass
