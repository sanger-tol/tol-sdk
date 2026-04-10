# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.elastic import ElasticDataSource


class TestElasticAggregator:
    def test_invalid_combination(self, mock_elastic_data_source: ElasticDataSource):
        aggregation_result = mock_elastic_data_source.get_aggregations(
            'obj_type',
            None,
            x_axis='field3',
            maximum_categories=8,
        )
        assert aggregation_result is None
