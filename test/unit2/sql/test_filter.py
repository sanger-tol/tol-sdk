# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from string import ascii_lowercase
from typing import List
from unittest.mock import MagicMock, PropertyMock, call

from tol.core import DataSourceFilter
from tol.sql.filter import DefaultDatabaseFilter


class MockComparator:
    """Takes a character, and returns it on equality comparison"""

    def __init__(self, c: str) -> None:
        self.__c = c

    def __eq__(self, __o: object) -> str:
        """(ugly hack) return the character on any equality (==) comparison"""
        return f'equal-{self.__c}'

    def __str__(self) -> str:
        return self.__c


class MockQuery:
    """Mocks a query, for filtering only."""

    def __init__(self) -> None:
        self.__filter_calls: List[call] = []

    @property
    def filter_calls(self) -> List[call]:
        return self.__filter_calls

    @property
    def filter_count(self) -> int:
        return len(self.__filter_calls)

    def filter(self, *args, **kwargs) -> MockQuery:  # noqa A003
        new_call = call(*args, **kwargs)
        self.__filter_calls.append(new_call)
        return self


class TestDefaultDatabaseFilter:
    def test_filter_none(self):
        """a DefaultDatabaseFilter given None doesn't do anything"""

        query = MockQuery()
        model = self.__get_mock_model()
        db_filter = DefaultDatabaseFilter(None)  # give it None
        query = db_filter.filter(query, 'test', {'test': model})
        assert query.filter_count == 0

    def test_filter_empty(self):
        """filter with no terms doesn't do anything"""

        query = MockQuery()
        model = self.__get_mock_model()
        ds_filter = DataSourceFilter()  # no terms
        db_filter = DefaultDatabaseFilter(ds_filter)
        query = db_filter.filter(query, 'test', {'test': model})
        assert query.filter_count == 0

    def test_filter_exact(self):
        """filter with only exact terms -> only equality filters"""

        exact = {
            c: c for c in ascii_lowercase
        }
        query = MockQuery()
        model = self.__get_mock_model()
        ds_filter = DataSourceFilter(exact=exact)
        db_filter = DefaultDatabaseFilter(ds_filter)
        query = db_filter.filter(query, 'test', {'test': model})

        assert query.filter_count == 26  # 26 letters in string.ascii_lowercase

        # `MockComparator().__eq__()` always returns the given character, prefixed
        # with "exact-". This is necessary, otherwise the value of __eq__(),
        # aka equality comparison, would almost always be `False`
        assert query.filter_calls == [
            call(f'equal-{c}') for c in ascii_lowercase
        ]

    def __get_mock_model(self) -> MagicMock:
        """Creates a MagicMock with tautological properties"""

        model = MagicMock()
        for c in ascii_lowercase:
            # for each lowercase ASCII letter, add a tautologically named property
            # to the class [e.g. model.a -> MockComparator('a'),
            # model.b -> MockComparator('b'), etc.]
            setattr(
                type(model),
                c,
                PropertyMock(return_value=MockComparator(c))
            )
        return model
