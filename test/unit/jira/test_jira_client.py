# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import responses

from tol.jira.client import JiraClient


FAKE_API_URL = 'http://test.lan/api'
FAKE_API_KEY = 'key'


class TestJiraClient:
    """The `JiraClient` and its methods"""

    @responses.activate
    def test_get_detail(self):
        """Default values, no token"""

        client = JiraClient(FAKE_API_URL, FAKE_API_KEY)
        objs = [
            {
                'key': f'KEY{i}',
                'id': f'{i}',
                'fields': {
                    'customField1': f'FIELD1{i}',
                    'customField2': f'FIELD2{i}'
                }
            }
            for i in range(1, 3)
        ]
        resp = {'total': 2, 'issues': objs}
        expected = [
            objs[0],
            objs[1]
        ]

        responses.get(
            f'{FAKE_API_URL}/rest/api/2/search',
            json=resp
        )

        observed = client.get_detail('issue', ['KEY1', 'KEY2'])
        assert observed == expected

    @responses.activate
    def test_get_fields(self):
        """Default values, no token"""

        client = JiraClient(FAKE_API_URL, FAKE_API_KEY)
        objs = [
            {
                'id': 'f',
                'name': 'FIELD',
                'clauseNames': ['customField'],
                'schema': {
                    'type': 'string'
                }
            }, {
                'id': 'f2',
                'name': 'FIELD2',
                'clauseNames': ['customField2'],
                'schema': {
                    'type': 'array',
                    'items': 'option'
                }
            }, {
                'id': 'u',
                'name': 'USER',
                'clauseNames': ['userField'],
                'schema': {
                    'type': 'user'
                }
            }
        ]
        resp = objs
        expected_fields = {
            'f': {
                'display_name': 'FIELD',
                'system_name': 'field',
                'type': 'str',
                'jira_type': 'string',
                'jira_item_type': 'string',
                'clause_name': 'customField',
                'relation': None
            },
            'f2': {
                'display_name': 'FIELD2',
                'system_name': 'field2',
                'type': 'List[str]',
                'jira_type': 'array',
                'jira_item_type': 'option',
                'clause_name': 'customField2',
                'relation': None
            },
            'u': {
                'display_name': 'USER',
                'system_name': 'user',
                'type': 'str',
                'jira_type': 'user',
                'jira_item_type': 'string',
                'clause_name': 'userField',
                'relation': 'user'
            }
        }

        responses.get(
            f'{FAKE_API_URL}/rest/api/latest/field',
            json=resp
        )

        fields = client.get_fields()
        assert fields == expected_fields
