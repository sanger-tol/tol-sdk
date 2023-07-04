# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.jira import JiraDataSource


class TestJiraDataSource:

    def test_init(self):
        """succesfully instantiates"""
        JiraDataSource(
            {
                'url': 'http://test/benchling',
                'api_token': '1234'
            }
        )
