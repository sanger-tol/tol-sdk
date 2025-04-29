# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
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

    # internal methods that still need to be concrete
    mock_sum._filter_by_source_type.side_effect = (
        lambda *args: Summariser._filter_by_source_type(mock_sum, *args)
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

        Summariser.resummarise_by_ids(
            mock_summariser,
            summary_objs,
            'second',
            'abc',
        )

        mock_summariser._summarise.assert_called_once_with(
            summary_objs[1],
            ext_and={
                'back_i.id': {
                    'in_list': {
                        'value': ['a', 'b', 'c']
                    }
                }
            }
        )

    def test_resummarise_by_ids__many_relationships(
        self,
        mock_summariser: Summariser,
        summary_objs: Iterable[DataObject],
    ) -> None:
        """Many relationships pointing to the target type"""

        Summariser.resummarise_by_ids(
            mock_summariser,
            summary_objs,
            'first',
            'efg',
        )

        assert mock_summariser._summarise.call_count == 2

        assert mock_summariser._summarise.call_args_list == [
            # first_one
            call(
                summary_objs[0],
                ext_and={
                    'first_one.id': {
                        'in_list': {
                            'value': ['e', 'f', 'g']
                        }
                    }
                }
            ),
            # do_not_forget_me
            call(
                summary_objs[0],
                ext_and={
                    'do_not_forget_me.id': {
                        'in_list': {
                            'value': ['e', 'f', 'g']
                        }
                    }
                }
            )
        ]
