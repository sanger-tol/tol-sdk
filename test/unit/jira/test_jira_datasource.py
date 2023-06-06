# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.jira import JiraDataSource


class MockJiraDataSource(JiraDataSource):
    pass


class TestJiraDataSource(TestCase):

    def test_get_by_id(self):
        jds = MockJiraDataSource({
            'url': 'http://test/benchling',
            'api_token': '1234'})

        with self.assertRaises(NotImplementedError):
            jds.get_by_id('object_type', 1)

    def test_get_list(self):
        jds = MockJiraDataSource({
            'url': 'http://test/benchling',
            'api_token': '1234'})

        with self.assertRaises(NotImplementedError):
            jds.get_list('object_type')

    def test_get_list_page(self):
        jds = MockJiraDataSource({
            'url': 'http://test/benchling',
            'api_token': '1234'})

        with self.assertRaises(NotImplementedError):
            jds.get_list_page('object_type', 1)

    def test_supported_types(self):
        jds = MockJiraDataSource({
            'url': 'http://test/benchling',
            'api_token': '1234'})

        with self.assertRaises(NotImplementedError):
            jds.supported_types

    def test_get_attribute_types(self):
        jds = MockJiraDataSource({
            'url': 'http://test/benchling',
            'api_token': '1234',
            'registry_id': '5678',
            'project_id': '6789',
            'entities': {}})

        with self.assertRaises(NotImplementedError):
            jds.get_attribute_types('object_type')
