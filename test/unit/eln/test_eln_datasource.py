# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import mock

from tol.eln import ElnDataSource


class MockElnDataSource(ElnDataSource):
    def _get_benchling_instance(self):
        self.benchling_instance = mock.Mock()

    def _format_results(self, results):
        return results


class TestElnDataSource:
    def test_instantiation(self):
        ElnDataSource(
            {
                'url': 'http://test/benchling',
                'api_key': '1234',
                'registry_id': '5678',
                'project_id': '6789',
                'entities': {}
            }
        )
