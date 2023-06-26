# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from string import ascii_lowercase
from typing import Any, List, Tuple
from unittest.mock import MagicMock, call

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


class MockColumn:
    """Mocks a column for various filter comparisons"""

    def __init__(self, key: str) -> None:
        self.__key = key

    def ilike(self, c: str) -> Tuple[str, str, str]:
        assert c.startswith('%'), f'"{c}" does not start with %'
        assert c.endswith('%'), f'"{c}" does not end with %'

        # remove the wildcard symbols
        return 'ilike', self.__key, c[1:-1]


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

    def test_filter_contains(self):
        """filter with only contains filters -> ilike filters"""

        class _MockModel:
            @classmethod
            def get_column(cls, name):
                return getattr(cls, name)

        _mock_model_class = type(
            '',
            (_MockModel,),
            {
                c: MockColumn(c) for c in ascii_lowercase
            }
        )
        query = MockQuery()

        contains_filter = {
            c: str(ord(c)) for c in ascii_lowercase
        }
        ds_filter = DataSourceFilter(contains=contains_filter)
        db_filter = DefaultDatabaseFilter(ds_filter)
        query: MockQuery = db_filter.filter(query, 'test', {'test': _mock_model_class})
        assert query.filter_count == 26  # 26 lower case letters
        assert query.filter_calls == [
            call(('ilike', c, str(ord(c))))
            for c in ascii_lowercase
        ]

    def test_filter_contains_wildcard(self):
        """wildcard chars must be escaped properly."""
        in_out_map = {
            'I contain % a percent sign': 'I contain \\% a percent sign',
            'this should not escape at all': 'this should not escape at all',
            'The truth is underscored by _': 'The truth is underscored by \\_',
            '_%_% __ ch%aos in this string!': '\\_\\%\\_\\% \\_\\_ ch\\%aos in this string!'
        }
        for in_, out_ in in_out_map.items():
            self.__assert_contains_equal(in_, out_)

    def test_filter_in_list(self):
        """Filtering by inclusion within a list of values"""

        class _MockModel:
            class _ComparatorColumn:  # noqa
                def __init__(self, name: str) -> None:
                    self.__name = name

                def in_(self, in_: List[Any]) -> Tuple[str, str, List[Any]]:
                    return 'in_', self.__name, in_

            id_luls = _ComparatorColumn('id_luls')  # noqa A003
            int_hype = _ComparatorColumn('int_hype')

            @classmethod
            def get_id_column_name(cls):
                return 'id_luls'

            @classmethod
            def get_column(cls, name):
                assert name in ['id_luls', 'int_hype']
                return getattr(cls, name)

        in_list = {
            'id': ['a', 'b', 'defence'],  # "id" not "id_luls"
            'int_hype': [None, 203, 3489, 1]
        }
        query = MockQuery()
        ds_filter = DataSourceFilter(in_list=in_list)
        db_filter = DefaultDatabaseFilter(ds_filter)
        query: MockQuery = db_filter.filter(query, 'test', {'test': _MockModel})

        assert query.filter_calls == [
            call(('in_', 'id_luls', ['a', 'b', 'defence'])),
            call(('in_', 'int_hype', [None, 203, 3489, 1]))
        ]

    def test_filter_range(self):
        """Filtering by a range of values works succesfully for various data types"""

        class _MockModel:
            class _ComparatorColumn:  # noqa
                def __init__(self, name: str) -> None:
                    self.__name = name

                def between(self, from_: Any, to_: Any) -> Tuple[str, str, str, str]:
                    return 'between', self.__name, from_, to_

            id = _ComparatorColumn('id')  # noqa A003
            datetime_hype = _ComparatorColumn('datetime_hype')

            @classmethod
            def get_id_column_name(cls):
                return 'id'

            @classmethod
            def get_column(cls, name):
                assert name in ['id', 'datetime_hype']
                return getattr(cls, name)

        ranges = {
            'id': {
                'from': 'lol',
                'to': 'extra-hype'
            },
            'datetime_hype': {
                'from': '1st of July',
                'to': 'Another date I guess?'
            }
        }
        query = MockQuery()
        ds_filter = DataSourceFilter(range=ranges)
        db_filter = DefaultDatabaseFilter(ds_filter)
        query: MockQuery = db_filter.filter(query, 'test', {'test': _MockModel})

        assert query.filter_calls == [
            call(('between', 'id', 'lol', 'extra-hype')),
            call(('between', 'datetime_hype', '1st of July', 'Another date I guess?'))
        ]

    def test_filter_default_id(self):
        """
        Filtering against "id" points to the correct column("id") if left as default
        """

        class _MockModel:
            class _ye_ol_id:  # noqa
                def __eq__(self, __o: object) -> str:
                    return 'filtered very! succesfully on the default ID'

            id = _ye_ol_id()  # noqa

            @classmethod
            def get_column(cls, name):
                assert name == 'id'
                return cls.id

            @classmethod
            def get_id_column_name(cls):
                return 'id'

        exact = {'id': 'hype_train'}
        query = MockQuery()
        ds_filter = DataSourceFilter(exact=exact)
        db_filter = DefaultDatabaseFilter(ds_filter)
        query = db_filter.filter(query, 'test', {'test': _MockModel})

        assert query.filter_calls == [
            call('filtered very! succesfully on the default ID')
        ]

    def test_filter_overriden_id(self):
        """
        Filtering against "id" points to the correct column if the name is overriden
        in a model definition.
        """

        class _MockModel:
            class _le_id_override:  # noqa
                def __eq__(self, __o: object) -> str:
                    return 'filtered very! succesfully on id_override'

            id_override = _le_id_override()

            @classmethod
            def get_id_column_name(cls):
                return 'id_override'

            @classmethod
            def get_column(cls, name):
                assert name == 'id_override'
                return cls.id_override

        exact = {'id': 'hype_train'}
        query = MockQuery()
        ds_filter = DataSourceFilter(exact=exact)
        db_filter = DefaultDatabaseFilter(ds_filter)
        query = db_filter.filter(query, 'test', {'test': _MockModel})

        assert query.filter_calls == [
            call('filtered very! succesfully on id_override')
        ]

    def __get_mock_model(self) -> MagicMock:
        """
        Creates a MagicMock for model that returns MockComparator for a
        given get_colum call.
        """

        model = MagicMock()
        type(model).get_column = lambda _, c: MockComparator(c)
        return model

    def __assert_contains_equal(self, in_: str, out_: str):
        """asserts that in_ is mapped to out_ within contains filter """

        class _MockModel:
            examine = MockColumn('examine')

            @classmethod
            def get_column(cls, name):
                assert name == 'examine'
                return cls.examine

        query = MockQuery()

        contains_filter = {'examine': in_}
        ds_filter = DataSourceFilter(contains=contains_filter)
        db_filter = DefaultDatabaseFilter(ds_filter)
        query: MockQuery = db_filter.filter(query, 'test', {'test': _MockModel})
        assert query.filter_count == 1
        assert query.filter_calls == [call(('ilike', 'examine', out_))]
