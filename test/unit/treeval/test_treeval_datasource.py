# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.treeval import TreevalDataSource


class TestTreevalDataSource:

    def test_init(self):
        """succesfully instantiates"""
        TreevalDataSource(
            {
                'url': 'http://test/jira',
                'api_token': '1234'
            }
        )
