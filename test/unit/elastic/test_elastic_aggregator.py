# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.elastic import ElasticDataSource


class TestElasticAggregator:
    def test_date_aggregation(self, mock_elastic_data_source: ElasticDataSource):
        # Mock the result of the Elastic API call
        mock_elastic_data_source.es.search.return_value = {
            'aggregations': {
                'date-aggregation': {
                    'buckets': [
                        {
                            'doc_count': 27,
                            'key': 1735689600,
                            'key_as_string': '2025-01-01',
                        },
                        {
                            'doc_count': 30,
                            'key': 1735776000,
                            'key_as_string': '2025-01-02',
                        }
                    ]
                }
            }
        }

        expected_result = [{
            'key': None,
            'data': [
                {
                    'x': '2025-01-01',
                    'y': 27,
                },
                {
                    'x': '2025-01-02',
                    'y': 30,
                },
            ]
        }]
        actual_result = mock_elastic_data_source._get_date_aggregation(
            'obj_type',
            None,
            'datefield',
            '1M',
        )
        assert actual_result == expected_result
        mock_elastic_data_source.es.search.assert_called_once()

    def test_scatter_aggregation(self, mock_elastic_data_source: ElasticDataSource):
        # TODO Once the scatter aggregation has been implemented
        pass

    def test_scatter_aggregation_cumulative(self, mock_elastic_data_source: ElasticDataSource):
        # TODO Once the scatter aggregation has been implemented
        pass
