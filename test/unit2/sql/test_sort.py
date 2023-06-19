# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import List
from unittest.mock import call

from tol.sql.sort import DefaultDatabaseSorter


class _MockModel:
    """Mocks a model, for sorting only"""

    class int_column:  # noqa N801
        @staticmethod
        def desc():
            return False

    @classmethod
    def get_column(cls, _):
        # only ever needs to return `int_column`
        return cls.int_column


class MockQuery:
    """Mocks a query, for sorting only."""

    def __init__(self) -> None:
        self.__sort_calls: List[call] = []

    @property
    def sort_calls(self) -> List[call]:
        return self.__sort_calls

    def order_by(self, *args, **kwargs) -> MockQuery:
        new_call = call(*args, **kwargs)
        self.__sort_calls.append(new_call)
        return self


class TestDefaultSorter:
    def test_ascending(self):
        """Without a hyphen leads to an ascending term"""

        sorter = DefaultDatabaseSorter('int_column')
        query = sorter.sort(
            MockQuery(),
            'test',
            {'test': _MockModel},
        )
        assert query.sort_calls == [
            call(_MockModel.int_column)
        ]

    def test_descending(self):
        """Leading hyphen -> strip and descending"""

        sorter = DefaultDatabaseSorter('-int_column')
        query = sorter.sort(
            MockQuery(),
            'test',
            {'test': _MockModel},
        )
        assert query.sort_calls == [
            call(_MockModel.int_column.desc())
        ]
