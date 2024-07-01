# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Any, Optional
from unittest.mock import Mock, create_autospec

from tol.core import DataObject, DataSource
from tol.core.data_source_dict import DataSourceDict
from tol.core.operator import Relational
from tol.core.relationship import RelationshipConfig
from tol.jira.converter import (
    JiraConverter
)
from tol.jira.parser import DefaultParser


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
    data_object.to_one_relationships = to_one
    return data_object


def _get_mock_data_source(
    attribute_types: dict[str, dict[str, Any]] = {},
    relationship_config: dict[str, RelationshipConfig] = {}
) -> DataSource:

    class __MockDataSourceRelational(DataSource, Relational):
        pass

    mock_ds = create_autospec(__MockDataSourceRelational, spec_set=True)

    mock_ds.attribute_types = attribute_types
    mock_ds.relationship_config = relationship_config
    mock_ds.supported_types = list(attribute_types.keys())
    mock_ds.data_object_factory = _get_mock_data_object

    return mock_ds


def _get_mock_ds_dict(
    attribute_types: dict[str, dict[str, Any]] = {},
    relationship_config: dict[str, RelationshipConfig] = {}
) -> dict[str, DataSource]:

    return DataSourceDict(
        _get_mock_data_source(
            attribute_types=attribute_types,
            relationship_config=relationship_config
        )
    )


class TestJiraConverter:
    """Tests `JiraConverter().convert()`"""

    def test_convert(self):
        """Test the converter"""

        in_ = [
            {
                'key': f'KEY{i}',
                'id': f'ID{i}',
                'fields': {
                    'customField1': f'FIELD_1{i}',
                    'customField2': f'FIELD_2{i}',
                    'customField3': f'2024-0{i}-0{i}T00:00:00.000+0000',
                    'customField4': i,
                    'customField5': [{'value': 'a'}, {'value': 'b'}],
                    'u': {
                        'name': f'USER{i}',
                        'emailAddress': f'user{i}@email',
                        'displayName': f'user{i}_display_name'
                    },
                    'created': f'2023-0{i}-0{i}T00:00:00.000+0000',
                },
                'changelog': {
                    'histories': [
                        {
                            'created': f'2024-0{i}-0{i}T00:00:00.000+0000',
                            'items': [
                                {
                                    'field': 'status',
                                    'fromString': f'status{i}',
                                    'toString': f'status{i+1}'
                                }
                            ]
                        },
                        {
                            'created': f'2024-0{i+1}-0{i+1}T00:00:00.000+0000',
                            'items': [
                                {
                                    'field': 'status',
                                    'fromString': f'status{i+1}',
                                    'toString': f'status{i+2}'
                                }
                            ]
                        }
                    ]
                }
            }
            for i in range(1, 3)
        ]
        field_mappings = {
            'key': {
                'system_name': 'key',
                'type': 'str'
            },
            'id': {
                'system_name': 'id',
                'type': 'str',
                'jira_type': 'string',
            },
            'customField1': {
                'system_name': 'custom_field_1',
                'type': 'str',
                'jira_type': 'string',
                'jira_item_type': 'string'
            },
            'customField2': {
                'system_name': 'custom_field_2',
                'type': 'str',
                'jira_type': 'string',
                'jira_item_type': 'string'
            },
            'customField3': {
                'system_name': 'custom_field_3',
                'type': 'datetime',
                'jira_type': 'datetime',
                'jira_item_type': 'string'
            },
            'customField4': {
                'system_name': 'custom_field_4',
                'type': 'float',
                'jira_type': 'number',
                'jira_item_type': 'string'
            },
            'customField5': {
                'system_name': 'custom_field_5',
                'type': 'float',
                'jira_type': 'array',
                'jira_item_type': 'option'
            }
        }
        parser = DefaultParser(
            _get_mock_ds_dict({
                'issue': {
                    'custom_field_1': 'str',
                    'custom_field_2': 'str',
                    'custom_field_3': 'datetime',
                    'custom_field_4': 'float',
                    'custom_field_5': 'List[str]',
                    'status_changes': 'List[dict[str, Any]]'
                },
                'user': {
                    'name': 'str',
                    'emailAddress': 'str',
                    'displayName': 'str'
                }
            }, {
                'issue': RelationshipConfig(to_one={
                    'u': 'user'
                })
            }),
            field_mappings
        )
        converter = JiraConverter(parser)
        (out_, _) = converter.convert_list(in_)
        assert len(out_) == 2
        first = out_[0]
        assert first.type == 'issue'
        assert first.id == 'KEY1'
        expected = {
            'custom_field_1': 'FIELD_11',
            'custom_field_2': 'FIELD_21',
            'custom_field_3': datetime(2024, 1, 1, 0, 0),
            'custom_field_4': 1,
            'custom_field_5': ['a', 'b'],
            'status_changes': [
                {
                    'this_status': 'status1',
                    'next_status': 'status2',
                    'start_date': datetime(2023, 1, 1, 0, 0),
                    'end_date': datetime(2024, 1, 1, 0, 0)
                },
                {
                    'this_status': 'status2',
                    'next_status': 'status3',
                    'start_date': datetime(2024, 1, 1, 0, 0),
                    'end_date': datetime(2024, 2, 2, 0, 0)
                }
            ]
        }
        assert first.attributes == expected
        assert first.to_one_relationships['u'].attributes == {
            'name': 'USER1',
            'emailAddress': 'user1@email',
            'displayName': 'user1_display_name'
        }
        second = out_[1]
        assert second.type == 'issue'
        assert second.id == 'KEY2'
        expected = {
            'custom_field_1': 'FIELD_12',
            'custom_field_2': 'FIELD_22',
            'custom_field_3': datetime(2024, 2, 2, 0, 0),
            'custom_field_4': 2,
            'custom_field_5': ['a', 'b'],
            'status_changes': [
                {
                    'this_status': 'status2',
                    'next_status': 'status3',
                    'start_date': datetime(2023, 2, 2, 0, 0),
                    'end_date': datetime(2024, 2, 2, 0, 0)
                },
                {
                    'this_status': 'status3',
                    'next_status': 'status4',
                    'start_date': datetime(2024, 2, 2, 0, 0),
                    'end_date': datetime(2024, 3, 3, 0, 0)
                }
            ]
        }
        assert second.attributes == expected
        assert second.to_one_relationships['u'].attributes == {
            'name': 'USER2',
            'emailAddress': 'user2@email',
            'displayName': 'user2_display_name'
        }
