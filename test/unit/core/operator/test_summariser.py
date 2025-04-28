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
) -> DataObject:

    mock_obj: DataObject = create_autospec(DataObject)

    mock_obj.type = 'summary'
    mock_obj.source_object_type = source_object_type
    mock_obj.destination_object_type = destination_object_type
    mock_obj.object_filters = filters

    mock_obj.attributes = {
        'source_object_type': source_object_type,
        'object_filters': filters,
        'destination_object_type': destination_object_type,
    }

    return mock_obj


def _mock_obj(
    object_type: str,
    object_id: str
) -> DataObject:

    obj: DataObject = create_autospec(DataObject)

    obj.id = object_id
    obj.type = object_type
    obj.attributes = {}

    return obj


def _mock_objs(
    object_type: str,
    object_ids: Iterable[str]
) -> list[DataObject]:

    return [
        _mock_obj(object_type, object_id)
        for object_id in object_ids
    ]


@pytest.fixture
def mock_summariser() -> Summariser:
    mock_sum: Summariser = create_autospec(
        Summariser,
        spec_set=True,
    )

    mock_sum.relationship_config = {
        'rel_a': RelationshipConfig(
            to_many={
                'first': 'first'
            }
        ),
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
            }
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
            }
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

        mock_summariser.get_by_ids.return_value = _mock_objs(
            'rel_i',
            'flarg',
        )

        Summariser.resummarise_by_ids(
            mock_summariser,
            summary_objs,
            'second',
            'abc',
        )

        mock_summariser._summarise.assert_called_once_with(
            summary_objs[1],
            ext_and={
                'le_second.id': {
                    'in_list': {
                        'value': ['f', 'l', 'a', 'r', 'g']
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
            # rel_a
            call(
                summary_objs[1:],
                source_object_type='first',
                ext_and=DataSourceFilter(
                    and_={
                        'a.id': {
                            'in_list': {
                                'value': ['e', 'f', 'g']
                            }
                        }
                    }
                )
            ),
            # back_b
            call(
                summary_objs[1:],
                source_object_type='first',
                ext_and=DataSourceFilter(
                    and_={
                        'b.id': {
                            'in_list': {
                                'value': ['e', 'f', 'g']
                            }
                        }
                    }
                )
            )
        ]
