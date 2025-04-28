# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

import pytest

from tol.core import DataObject, DataSourceFilter
from tol.core.operator import Summariser


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

    def test_resummarise_by_ids(
        self,
        mock_summariser: Summariser,
        summary_objs: Iterable[DataObject],
    ) -> None:

        #TODO - this needs to be WAY more complicated

        Summariser.resummarise_by_ids(
            mock_summariser,
            summary_objs,
            'second',
            list('abc')
        )

        mock_summariser._summarise.assert_called_once_with(
            summary_objs[1:],
            source_object_type='second',
            source_object_ids=['a', 'b', 'c']
        )
