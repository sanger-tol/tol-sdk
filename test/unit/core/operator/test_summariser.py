# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterable
from unittest.mock import call, create_autospec

import pytest

from tol.core import DataObject, DataSourceFilter
from tol.core.operator import Summariser
from tol.core.relationship import RelationshipConfig


def __mock_summary(
    source_object_type: str,
    destination_object_type: str,
    filters: DataSourceFilter,
    group_by_first: str,
) -> DataObject:

    mock_obj: DataObject = create_autospec(DataObject)

    mock_obj.type = 'summary'
    mock_obj.source_object_type = source_object_type
    mock_obj.destination_object_type = destination_object_type
    mock_obj.object_filters = filters
    mock_obj.group_by = [group_by_first]

    return mock_obj


@pytest.fixture
def mock_summariser() -> Summariser:
    mock_sum: Summariser = create_autospec(
        Summariser,
        spec_set=True,
    )

    mock_sum.relationship_config = {
        'rel_a': RelationshipConfig(
            to_many={
                'first_one': 'first',
                'do_not_forget_me': 'first',
            }
        ),
        # irrelevant alternative
        'rel_b': RelationshipConfig(
            to_many={
                'le_first': 'first'
            }
        ),
        'first': RelationshipConfig(
            to_one={
                'back_a': 'rel_a',
                'back_b': 'rel_b',
            }
        ),
        'rel_i': RelationshipConfig(
            to_many={
                'le_second': 'second'
            }
        ),
        'second': RelationshipConfig(
            to_one={
                'back_i': 'rel_i',
            }
        ),
    }

    def __mock_obj(
        to_one_name: str,
        to_one_id: str,
    ) -> DataObject:

        mock_obj: DataObject = create_autospec(
            DataObject,
            spec_set=True
        )

        def __get_field_by_name(field_name: str) -> Any:
            assert field_name == f'{to_one_name}.id'
            return to_one_id

        mock_obj.get_field_by_name.side_effect = __get_field_by_name

        return mock_obj

    def __get_by_ids(
        object_type: str,
        object_ids: Iterable[str],
        **kwargs
    ):

        rel_name = 'back_a' if object_type == 'first' else 'back_i'

        return [
            __mock_obj(
                rel_name,
                f'rel_{id_}'
            )
            for id_ in object_ids
        ]

    mock_sum.get_by_ids.side_effect = __get_by_ids

    # internal methods that still need to be concrete
    mock_sum._filter_by_source_type.side_effect = (
        lambda *args: Summariser._filter_by_source_type(mock_sum, *args)
    )
    mock_sum._ext_and_for_relationship.side_effect = (
        lambda *args: Summariser._ext_and_for_relationship(mock_sum, *args)
    )
    mock_sum._get_resummarised_to_one_names.side_effect = (
        lambda *args: Summariser._get_resummarised_to_one_names(mock_sum, *args)
    )

    # get_objects_to_summarise method is tested elsewhere
    # but we need to mock it here
    mock_sum.get_and_filter_to_summarise.side_effect = (
        Summariser.get_and_filter_to_summarise.__get__(mock_sum)
    )

    return mock_sum


@pytest.fixture
def summary_objs() -> Iterable[DataObject]:
    return [
        __mock_summary(
            'first',
            'rel_a',
            {
                'anything': {
                    'eq': {
                        'value': True
                    }
                }
            },
            'back_a.id'
        ),
        __mock_summary(
            'second',
            'rel_i',
            {
                'please': {
                    'eq': {
                        'value': 'no'
                    }
                }
            },
            'back_i.important_column'
        )
    ]


class TestSummariser:

    def test_summarise_all(
        self,
        mock_summariser: Summariser,
        summary_objs: Iterable[DataObject],
    ) -> None:

        Summariser.summarise_all(
            mock_summariser,
            summary_objs,
        )

        assert mock_summariser._summarise.call_args_list == [
            call(summary_objs[0]),
            call(summary_objs[1]),
        ]

    def test_summarise_type(
        self,
        mock_summariser: Summariser,
        summary_objs: Iterable[DataObject],
    ) -> None:

        Summariser.summarise_type(
            mock_summariser,
            summary_objs,
            'second',
        )

        mock_summariser._summarise.assert_called_once_with(
            summary_objs[1]
        )

    def test_resummarise_by_ids__simple(
        self,
        mock_summariser: Summariser,
        summary_objs: Iterable[DataObject],
    ) -> None:
        """Only one relationship"""

        ret = Summariser.resummarise_by_ids(
            mock_summariser,
            summary_objs,
            'second',
            'abc',
        )
        (((observed_summary,), kwargs),) = mock_summariser._summarise.call_args_list

        assert observed_summary == summary_objs[1]
        assert len(kwargs) == 1
        assert set(kwargs['ext_and']['back_i.id']['in_list']['value']) == {
            'rel_a',
            'rel_b',
            'rel_c',
        }
        assert ret == {
            'rel_i': {'rel_a', 'rel_b', 'rel_c'},
        }

    def test_resummarise_by_ids__many_relationships(
        self,
        mock_summariser: Summariser,
        summary_objs: Iterable[DataObject],
    ) -> None:
        """Many relationships pointing to the target type"""

        ret = Summariser.resummarise_by_ids(
            mock_summariser,
            summary_objs,
            'first',
            'efg',
        )

        (((observed_summary,), kwargs),) = mock_summariser._summarise.call_args_list

        assert observed_summary == summary_objs[0]
        assert len(kwargs) == 1
        assert set(kwargs['ext_and']['back_a.id']['in_list']['value']) == {
            'rel_e',
            'rel_f',
            'rel_g',
        }
        assert ret == {
            'rel_a': {'rel_e', 'rel_f', 'rel_g'},
        }
