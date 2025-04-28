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
    filters: DataSourceFilter,
) -> DataObject:

    mock_obj: DataObject = create_autospec(DataObject)

    mock_obj.type = 'summary'
    mock_obj.source_object_type = source_object_type
    mock_obj.object_filters = filters

    mock_obj.attributes = {
        'source_object_type': source_object_type,
        'object_filters': filters,
    }

    return mock_obj


@pytest.fixture
def mock_summariser() -> Summariser:
    mock_sum: Summariser = create_autospec(
        Summariser,
        spec_set=True,
    )

    mock_sum.relationship_config = {
        'rel_a': RelationshipConfig(
            to_one={
                'a': 'first'
            }
        ),
        'rel_b': RelationshipConfig(
            to_one={
                'b': 'first'
            }
        ),
        'first': RelationshipConfig(
            to_many={
                'back_a': 'a',
                'back_b': 'b',
            }
        ),
        'rel_i': RelationshipConfig(
            to_one={
                'i': 'second'
            }
        ),
        'second': RelationshipConfig(
            to_many={
                'back_i': 'i',
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
            DataSourceFilter(
                and_={
                    'anything': {
                        'eq': {
                            'value': True
                        }
                    }
                }
            )
        ),
        __mock_summary(
            'second',
            DataSourceFilter(
                and_={
                    'please': {
                        'eq': {
                            'value': 'no'
                        }
                    }
                }
            )
        )
    ]


class TestSummariser:

    def test_summarse_all(
        self,
        mock_summariser: Summariser,
        summary_objs: Iterable[DataObject],
    ) -> None:

        Summariser.summarse_all(
            mock_summariser,
            summary_objs,
        )

        mock_summariser._summarise.assert_called_once_with(
            summary_objs
        )

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
            summary_objs[1:],
            source_object_type='second'
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
            summary_objs[1:],
            source_object_type='second',
            source_object_ids=['a', 'b', 'c']
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
            # rel_a
            call(
                summary_objs[1:],
                source_object_type='first',
                ext_and=DataSourceFilter(
                    and_={
                        'rel_a.id': {
                            'in_list': {
                                'value': ['e', 'f', 'g']
                            }
                        }
                    }
                )
            ),
            # rel_b
            call(
                summary_objs[1:],
                source_object_type='first',
                ext_and=DataSourceFilter(
                    and_={
                        'rel_b.id': {
                            'in_list': {
                                'value': ['e', 'f', 'g']
                            }
                        }
                    }
                )
            )
        ]
