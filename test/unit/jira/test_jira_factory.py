# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Any, Optional
from unittest.mock import Mock

import responses

from tol.core import DataObject
from tol.jira import create_jira_datasource


FAKE_API_URL = 'http://fake.lan/api'
FAKE_API_KEY = 'key'


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: dict[str, Any] = {},
    to_one: dict[str, Any] = {}
) -> DataObject:

    data_object = Mock()

    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes
    data_object._to_one_objects = to_one

    return data_object


class TestCreateJiraDatasource:
    """larger-than unit tests on `create_jira_datasource`"""

    @responses.activate
    def test_get_by_id(self):
        """`create_jira_datasource().get_by_id()` + no token"""

        responses.get(
            f'{FAKE_API_URL}/rest/api/latest/field',
            json=[{
                'id': 'customField1',
                'type': 'string',
                'name': 'Custom Field 1'
            }]
        )

        jira_ds = create_jira_datasource(
            FAKE_API_URL,
            FAKE_API_KEY
        )

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='issue',
            id_='KEY1'
        )
        mock_do_factory.return_value = mock_data_object
        jira_ds.data_object_factory = mock_do_factory

        in_ = {
            'total': 1,
            'issues': [{
                'key': 'KEY1',
                'fields': {
                    'customField1': 'FIELD1',
                    'created': '2024-01-01T00:00:00.000+0000'
                },
                'changelog': {
                    'histories': [{
                        'items': [{
                            'field': 'status',
                            'fromString': 'status1',
                            'toString': 'status2'
                        }],
                        'created': '2024-02-02T00:00:00.000+0000'
                    }]
                }
            }]
        }

        responses.get(
            f'{FAKE_API_URL}/rest/api/2/search',
            json=in_
        )

        observed = list(jira_ds.get_by_id('issue', ['KEY1']))
        mock_do_factory.assert_called_once_with(
            'issue',
            id_='KEY1',
            attributes={
                'custom_field_1': 'FIELD1',
                'status_changes': [{
                    'this_status': 'status1',
                    'next_status': 'status2',
                    'start_date': datetime(2024, 1, 1, 0, 0, 0),
                    'end_date': datetime(2024, 2, 2, 0, 0, 0)
                }]
            },
            to_one={}
        )
        assert observed == [mock_data_object]

    @responses.activate
    def test_get_by_id_multiple(self):
        """
        Multiple statuses, one of which is not found + token
        """

        responses.get(
            f'{FAKE_API_URL}/rest/api/latest/field',
            json=[{
                'id': 'customField1',
                'type': 'string',
                'name': 'Custom Field 1'
            }]
        )

        api_ds = create_jira_datasource(
            FAKE_API_URL,
            FAKE_API_KEY
        )

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='issue',
            id_='KEY1'
        )
        mock_do_factory.return_value = mock_data_object
        api_ds.data_object_factory = mock_do_factory

        in_ = {
            'total': 1,
            'issues': [{
                'key': 'KEY1',
                'fields': {
                    'customField1': 'FIELD1',
                    'created': '2024-01-01T00:00:00.000+0000'
                },
                'changelog': {
                    'histories': [{
                        'items': [{
                            'field': 'status',
                            'fromString': 'status1',
                            'toString': 'status2'
                        }],
                        'created': '2024-02-02T00:00:00.000+0000'
                    }]
                }
            }]
        }

        responses.get(
            f'{FAKE_API_URL}/rest/api/2/search',
            json=in_
        )

        observed = list(
            api_ds.get_by_id('issue', ['404', 'KEY1'])
        )
        mock_do_factory.assert_called_once_with(
            'issue',
            id_='KEY1',
            attributes={
                'custom_field_1': 'FIELD1',
                'status_changes': [{
                    'this_status': 'status1',
                    'next_status': 'status2',
                    'start_date': datetime(2024, 1, 1, 0, 0, 0),
                    'end_date': datetime(2024, 2, 2, 0, 0, 0)
                }]
            },
            to_one={}
        )
        assert observed == [None, mock_data_object]
