# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterable
from unittest.mock import create_autospec

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
def mock_summariser_to_get_objects() -> Summariser:
    mock_sum: Summariser = create_autospec(
        Summariser,
        spec_set=True,
    )

    mock_sum.relationship_config = {
        'rel_a': RelationshipConfig(
            to_many={
                'first_one': 'first',
            }
        ),
        'first': RelationshipConfig(
            to_one={
                'back_a': 'rel_a',
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
        return [
            __mock_obj(
                'back_a',
                f'rel_{id_}'
            )
            for id_ in object_ids
        ]

    mock_sum.get_by_ids.side_effect = __get_by_ids

    mock_sum._filter_by_source_type.side_effect = (
        lambda *args: Summariser._filter_by_source_type(mock_sum, *args)
    )
    mock_sum._ext_and_for_relationship.side_effect = (
        lambda *args: Summariser._ext_and_for_relationship(mock_sum, *args)
    )
    mock_sum._get_resummarised_to_one_names.side_effect = (
        lambda *args: Summariser._get_resummarised_to_one_names(mock_sum, *args)
    )

    return mock_sum


@pytest.fixture
def summary_obj() -> DataObject:
    return __mock_summary(
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
    )


class TestGetObjectsToSummarise:

    def test_get_objects_to_summarise(
        self,
        mock_summariser_to_get_objects: Summariser,
        summary_obj: DataObject,
    ) -> None:

        ext_and = Summariser.get_and_filter_to_summarise(
            mock_summariser_to_get_objects,
            summary_obj,
            'first',
            ['a', 'b', 'c']
        )

        assert summary_obj.source_object_type == 'first'
        assert 'back_a.id' in ext_and

        observed = ext_and['back_a.id']['in_list']['value']
        assert len(observed) == 3
        assert set(observed) == {'rel_a', 'rel_b', 'rel_c'}

    def test_get_objects_to_summarise_no_matching_summaries(
        self,
        mock_summariser_to_get_objects: Summariser,
        summary_obj: DataObject,
    ) -> None:

        original_side_effect = mock_summariser_to_get_objects._filter_by_source_type.side_effect
        mock_summariser_to_get_objects._filter_by_source_type.side_effect = lambda *args: []

        try:
            Summariser.get_and_filter_to_summarise(
                mock_summariser_to_get_objects,
                summary_obj,
                'non_existent_type',
                ['a', 'b']
            )
        finally:
            mock_summariser_to_get_objects._filter_by_source_type.side_effect = (
                original_side_effect
            )
