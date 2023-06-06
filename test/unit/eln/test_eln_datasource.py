# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase, mock)

from tol.eln import ElnDataSource


class MockElnDataSource(ElnDataSource):
    def _get_benchling_instance(self):
        self.benchling_instance = mock.Mock()

    def _format_results(self, results):
        return results


class TestElnDataSource(TestCase):

    def test_get_by_id(self):
        eds = MockElnDataSource({
            'url': 'http://test/benchling',
            'api_key': '1234',
            'registry_id': '5678',
            'project_id': '6789',
            'entities': {}})

        with self.assertRaises(NotImplementedError):
            eds.get_by_id('object_type', 1)

    def test_get_list(self):
        eds = MockElnDataSource({
            'url': 'http://test/benchling',
            'api_key': '1234',
            'registry_id': '5678',
            'project_id': '6789',
            'entities': {}})

        with self.assertRaises(NotImplementedError):
            eds.get_list('object_type')

    def test_get_list_page(self):
        eds = MockElnDataSource({
            'url': 'http://test/benchling',
            'api_key': '1234',
            'registry_id': '5678',
            'project_id': '6789',
            'entities': {}})

        with self.assertRaises(NotImplementedError):
            eds.get_list_page('object_type', 1)

    def test_supported_types(self):
        eds = MockElnDataSource({
            'url': 'http://test/benchling',
            'api_key': '1234',
            'registry_id': '5678',
            'project_id': '6789',
            'entities': {}})

        with self.assertRaises(NotImplementedError):
            eds.supported_types

    def test_get_attribute_types(self):
        eds = MockElnDataSource({
            'url': 'http://test/benchling',
            'api_key': '1234',
            'registry_id': '5678',
            'project_id': '6789',
            'entities': {}})

        with self.assertRaises(NotImplementedError):
            eds.get_attribute_types('object_type')
