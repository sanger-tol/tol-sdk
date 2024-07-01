# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock

import pytest

from tol.core import (
    DataObject,
    DataSourceError
)
from tol.core.relationship import RelationshipConfig
from tol.jira import JiraDataSource


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


class TestJiraDataSource:
    def test_get_by_id_found(self):
        """200 response, no token"""

        mock_client = Mock()

        mock_response = {
            'key': {'system_name': 'key', 'type': 'str', 'relation': None},
            'customField1': {'system_name': 'custom_field_1', 'type': 'str', 'relation': None},
            'customField2': {'system_name': 'custom_field_2', 'type': 'str', 'relation': None}
        }
        mock_client.get_fields.return_value = mock_response
        mock_response = {'key': 'KEY1', 'customField1': 'FIELD1', 'customField2': 'FIELD2'}
        mock_client.get_detail.return_value = [mock_response]

        mock_lc_converter = Mock()

        ds = JiraDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter,
            None,
            None
        )
        ds.data_object_factory = lambda: Mock()

        mock_data_object = _get_mock_data_object(
            type_='issue',
            id_='KEY1',
            attributes={'customField1': 'FIELD1', 'customField2': 'FIELD2'}
        )
        mock_lc_converter.convert_list.return_value = ([mock_data_object], 1)

        (observed,) = list(ds.get_by_id('issue', ['KEY1']))
        assert observed == mock_data_object

        mock_client.get_detail.assert_called_once_with(
            'issue',
            ['KEY1']
        )
        mock_lc_converter.convert_list.assert_called_once_with(
            [mock_response]
        )

    def test_get_by_id_not_found(self):
        """404 response"""

        mock_client = Mock()

        # mock a 404 returning `None`
        mock_client.get_detail.return_value = []
        mock_response = {
            'key': {'system_name': 'key', 'type': 'str', 'relation': None},
            'customField1': {'system_name': 'custom_field_1', 'type': 'str', 'relation': None},
            'customField2': {'system_name': 'custom_field_2', 'type': 'str', 'relation': None}
        }
        mock_client.get_fields.return_value = mock_response

        mock_lc_converter = Mock()
        mock_lc_converter.convert_list.return_value = ([], 0)

        ds = JiraDataSource(
            lambda: mock_client,
            lambda: mock_lc_converter,
            None,
            None
        )
        ds.data_object_factory = lambda: Mock()

        (observed,) = list(ds.get_by_id('issue', ['KEY1']))
        assert observed is None

        mock_client.get_detail.assert_called_once_with(
            'issue',
            ['KEY1']
        )
        mock_lc_converter.convert_list.assert_called_once_with(
            []
        )

    def test_bad_object_type(self):
        """A bad object type -> raise `DataSourceError()`"""
        mock_client = Mock()

        # mock a 404 returning `None`
        mock_client.get_detail.return_value = []
        mock_response = {
            'key': {'system_name': 'key', 'type': 'str', 'relation': None},
            'customField1': {'system_name': 'custom_field_1', 'type': 'str', 'relation': None},
            'customField2': {'system_name': 'custom_field_2', 'type': 'str', 'relation': None}
        }
        mock_client.get_fields.return_value = mock_response

        ds = JiraDataSource(
            lambda: mock_client,
            lambda: None,
            None,
            None
        )
        with pytest.raises(DataSourceError):
            list(ds.get_by_id('test', ['does not matter at all']))

    def test_get_list_page_empty(self):
        """
        `JiraDataSource().get_list_page()` gets empty list
        from client. `filter` and `sort_by` are not `None`,
        and fully populated.
        """

        mock_json = Mock()

        mock_client = Mock()
        mock_client.config_attribute_types.return_value = {
            'test': {}
        }
        mock_client.get_list_page.return_value = (mock_json, 84959859)
        mock_response = {
            'key': {'system_name': 'key', 'type': 'str', 'relation': None},
            'customField1': {'system_name': 'custom_field_1', 'type': 'str', 'relation': None},
            'customField2': {'system_name': 'custom_field_2', 'type': 'str', 'relation': None}
        }
        mock_client.get_fields.return_value = mock_response
        mock_converter = Mock()
        mock_converter.convert_list.return_value = ([], 0)

        mock_ds_filter = Mock()

        mock_filter = Mock()
        mock_filter.dumps.return_value = 'key = "ISSUE-1234"'

        mock_sorter = Mock()
        mock_sorter.sort.return_value = 'ORDER BY custom_field_2 DESC'

        jira_ds = JiraDataSource(
            lambda: mock_client,
            lambda: mock_converter,
            lambda: mock_filter,
            lambda: mock_sorter
        )

        observed = jira_ds.get_list_page(
            'test',
            3489,
            page_size=8989,
            object_filters=mock_ds_filter,
            sort_by='-custom_field_2'
        )

        mock_client.get_list_page.assert_called_once_with(
            'test',
            page=3489,
            page_size=8989,
            filter_string='key = "ISSUE-1234" ORDER BY custom_field_2 DESC'
        )
        mock_filter.dumps.assert_called_once_with(
            mock_ds_filter
        )
        mock_sorter.sort.assert_called_once_with(
            '-custom_field_2'
        )
        mock_converter.convert_list.assert_called_once_with(
            mock_json
        )

        assert observed == ([], 84959859)

    def test_get_list_page_populated(self):
        """
        `JiraDataSource().get_list_page()` gets populated list
        from client. `filter` and `sort_by` are `None`
        """

        mock_objs = [Mock() for _ in range(3)]

        mock_json = Mock()

        mock_client = Mock()
        mock_client.config_attribute_types.return_value = {
            'test': {}
        }
        mock_client.get_list_page.return_value = (mock_json, 200)
        mock_response = {
            'key': {'system_name': 'key', 'type': 'str', 'relation': None},
            'customField1': {'system_name': 'custom_field_1', 'type': 'str', 'relation': None},
            'customField2': {'system_name': 'custom_field_2', 'type': 'str', 'relation': None}
        }
        mock_client.get_fields.return_value = mock_response
        mock_converter = Mock()
        mock_converter.convert_list.return_value = (mock_objs, 6)

        mock_filter = Mock()
        mock_sorter = Mock()
        mock_sorter.sort.return_value = 'ORDER BY key ASC'

        jira_ds = JiraDataSource(
            lambda: mock_client,
            lambda: mock_converter,
            lambda: mock_filter,
            lambda: mock_sorter
        )

        observed = jira_ds.get_list_page(
            'test',
            101,
            page_size=3,
        )

        mock_client.get_list_page.assert_called_once_with(
            'test',
            page=101,
            page_size=3,
            filter_string='ORDER BY key ASC'
        )
        mock_filter.dumps.assert_not_called()
        mock_sorter.sort.assert_called_once_with(
            None
        )
        mock_converter.convert_list.assert_called_once_with(
            mock_json
        )

        assert observed == (mock_objs, 200)

    def test_supported_types(self):
        expected = ['issue', 'user']
        mock_client = Mock()
        mock_response = {}

        mock_client.get_fields.return_value = mock_response
        ds = JiraDataSource(
            lambda: mock_client,
            None,
            None,
            None
        )

        observed = ds.supported_types

        assert observed == expected

    def test_attribute_types(self):
        expected = {
            'issue': {
                'key': 'str',
                'custom_field_1': 'List[str]',
                'custom_field_2': 'float',
                'status_changes': 'List[Dict[str, Any]]'
            },
            'user': {
                'name': 'str',
                'emailAddress': 'str',
                'displayName': 'str'
            }
        }
        mock_client = Mock()
        mock_response = {
            'key': {'system_name': 'key', 'type': 'str', 'relation': None},
            'customField1': {
                'system_name': 'custom_field_1',
                'type': 'List[str]',
                'relation': None
            },
            'customField2': {
                'system_name': 'custom_field_2',
                'type': 'float',
                'relation': None
            }
        }

        mock_client.get_fields.return_value = mock_response
        ds = JiraDataSource(
            lambda: mock_client,
            None,
            None,
            None
        )

        observed = ds.attribute_types

        assert observed == expected

    def test_relationship_config(self):
        expected = {
            'issue': RelationshipConfig(to_one={
                'u1': 'user',
                'u2': 'user',
            })
        }
        mock_client = Mock()
        mock_response = {
            'u1': {'system_name': 'u1', 'type': 'user', 'relation': 'user'},
            'u2': {'system_name': 'u2', 'type': 'user', 'relation': 'user'},
        }

        mock_client.get_fields.return_value = mock_response
        ds = JiraDataSource(
            lambda: mock_client,
            None,
            None,
            None
        )

        observed = ds.relationship_config

        assert observed == expected
