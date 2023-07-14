# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from string import ascii_lowercase
from typing import Any
from unittest.mock import MagicMock

import pytest

from sqlalchemy.exc import IntegrityError

from tol.core import DataSourceError
from tol.sql.database import DefaultDatabase


class _Column:
    def __init__(self, name: Any) -> None:
        self.__name = name

    def __eq__(self, __v: Any) -> tuple(str, str, Any):
        """gives a deterministic result for __eq__ (==)"""
        return '__eq__', self.__name, __v


class _TestModel:

    id = _Column('id')  # noqa A003
    int_column = _Column('int_column')

    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get_table_name(cls):
        return 'test'

    @classmethod
    def get_id_column_name(cls):
        return 'id'

    @property
    def instance_id(self):
        pass


class _OverrideIdModel:
    id_other = _Column('id_other')

    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get_id_column_name(cls) -> str:
        return 'id_other'

    @classmethod
    def get_table_name(cls) -> str:
        return 'test_override'


class _SessionMock:
    """Mocks an SqlAlchemy session"""
    def __init__(self, return_value: Any) -> None:
        self.__return_value = return_value
        self.__calls: list[
            tuple[str, tuple[Any], dict[str, Any]]
        ] = []

    @property
    def calls(self) -> list[
        tuple[str, tuple[Any], dict[str, Any]]
    ]:
        return self.__calls

    @property
    def calls_dict(self) -> dict[
        str,
        list[tuple[str, tuple[Any], dict[str, Any]]]
    ]:
        __d = {}
        for c in self.__calls:
            __k = c[0]
            c_list = __d.get(__k, [])
            c_list.append(c)
            __d[__k] = c_list
        return __d

    def filter(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('filter', args, kwargs))
        return self

    def query(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('query', args, kwargs))
        return self

    def limit(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('limit', args, kwargs))
        return self

    def delete(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('delete', args, kwargs))
        return self

    def commit(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('commit', args, kwargs))
        return self

    def offset(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('offset', args, kwargs))
        return self

    def one_or_none(self, *args, **kwargs) -> Any:
        self.__calls.append(('one_or_none', args, kwargs))
        return self.__return_value

    def all(self, *args, **kwargs) -> None:  # noqa
        self.__calls.append(('all', args, kwargs))
        return self.__return_value

    def close(self, *args, **kwargs) -> None:
        pass

    def count(self, *args, **kwargs) -> int:
        self.__calls.append(('count', args, kwargs))
        # this is not remotely type safe
        return len(self.__return_value)


class TestDefaultDatabase:
    def test_get_by_id_not_found(self):
        """get_by_id() gets a non-existent row -> return None"""

        session_mock = _SessionMock(None)
        db = DefaultDatabase(lambda: session_mock, [_TestModel])
        result = db.get_by_id('test', '404')
        assert result is None
        # 3 = 1 query + 1 filter + 1 one_or_none
        assert len(session_mock.calls) == 3
        # query on correct table
        assert session_mock.calls[0] == ('query', (_TestModel,), {})
        # filter correct column
        assert session_mock.calls[1] == (
            'filter',
            (_TestModel.id == '404',),
            {}
        )
        # finally one_or_none
        assert session_mock.calls[2] == ('one_or_none', (), {})

    def test_get_by_id_exists(self):
        """get_by_id() gets an existing row -> return it"""

        expected = _TestModel(
            id='302'
        )
        session_mock = _SessionMock(expected)
        db = DefaultDatabase(lambda: session_mock, [_TestModel])
        result = db.get_by_id('test', '302')
        assert result == expected
        # 3 = 1 query + 1 filter + 1 one_or_none
        assert len(session_mock.calls) == 3
        # query on correct table
        assert session_mock.calls[0] == ('query', (_TestModel,), {})
        # filter correct column
        assert session_mock.calls[1] == (
            'filter',
            (_TestModel.id == '302',),
            {}
        )
        # finally one_or_none
        assert session_mock.calls[2] == ('one_or_none', (), {})

    def test_get_by_non_standard_id_column(self):
        """get_by_id using a different id_column"""

        expected = _OverrideIdModel(id_other='302')
        session_mock = _SessionMock(expected)
        db = DefaultDatabase(lambda: session_mock, [_OverrideIdModel])
        result = db.get_by_id('test_override', '302')
        assert result == expected
        # 3 = 1 query + 1 filter + 1 one_or_none
        assert len(session_mock.calls) == 3
        # query on correct table
        assert session_mock.calls[0] == ('query', (_OverrideIdModel,), {})
        # filter correct column
        assert session_mock.calls[1] == (
            'filter',
            (_OverrideIdModel.id_other == '302',),
            {}
        )
        # finally one_or_none
        assert session_mock.calls[2] == ('one_or_none', (), {})

    def test_get_list_page_none_found(self):
        """get_list_page that returns no results at all, no filters"""

        session_mock = _SessionMock([])
        db = DefaultDatabase(lambda: session_mock, [_TestModel])
        result = db.get_page(
            'test',
            offset=300,
            limit=100
        )
        assert list(result) == []
        # 4 = query + limit + offset + all
        assert len(session_mock.calls) == 4
        # query on correct table
        assert session_mock.calls[0] == ('query', (_TestModel,), {})
        # NB. using calls_dict as it doesn't matter which order
        # limit and offset occur.

        # limit correctly
        assert session_mock.calls_dict['limit'] == [
            ('limit', (100,), {})
        ]
        # offset correctly
        assert session_mock.calls_dict['offset'] == [
            ('offset', (300,), {})
        ]
        # finally all()
        assert session_mock.calls[-1] == ('all', (), {})

    def test_get_list_page_some(self):
        """get_list_page that does find some results, and returns them"""

        expected = [
            _TestModel(id=i)
            for i in range(300, 400)
        ]
        session_mock = _SessionMock(expected)
        db = DefaultDatabase(lambda: session_mock, [_TestModel])
        result = db.get_page(
            'test',
            offset=300,
            limit=100
        )
        assert list(result) == expected
        # 4 = query + limit + offset + all
        assert len(session_mock.calls) == 4
        # query on correct table
        assert session_mock.calls[0] == ('query', (_TestModel,), {})
        # NB. using calls_dict as it doesn't matter which order
        # limit and offset occur.

        # limit correctly
        assert session_mock.calls_dict['limit'] == [
            ('limit', (100,), {})
        ]
        # offset correctly
        assert session_mock.calls_dict['offset'] == [
            ('offset', (300,), {})
        ]
        # finally all()
        assert session_mock.calls[-1] == ('all', (), {})

    def test_count_no_results(self):
        """count() works with no results (no filters) -> returns 0"""

        session_mock = _SessionMock([])
        db = DefaultDatabase(lambda: session_mock, [_TestModel])
        result = db.count('test')
        assert result == 0
        # 2 = query + count
        assert len(session_mock.calls) == 2
        # query first
        assert session_mock.calls[0] == ('query', (_TestModel,), {})
        # then count
        assert session_mock.calls[1] == ('count', (), {})

    def test_count_results_found(self):
        """count() works with some results found (no filters)"""

        expected = list(range(234))
        session_mock = _SessionMock(expected)
        db = DefaultDatabase(lambda: session_mock, [_TestModel])
        result = db.count('test')
        assert result == 234
        # 2 = query + count
        assert len(session_mock.calls) == 2
        # query first
        assert session_mock.calls[0] == ('query', (_TestModel,), {})
        # then count
        assert session_mock.calls[1] == ('count', (), {})

    def test_delete_integrity_error(self):
        """
        `Model().delete()` raises `IntegrityError` -> intercepted, and an
        appropriate `DataSourceError` is raised instead.
        """

        class _IntegrityErrorSession(_SessionMock):
            def commit(self, *args, **kwargs) -> None:
                raise IntegrityError(
                    MagicMock(),
                    MagicMock(),
                    MagicMock()
                )

        class _IntegrityErrorModel(_TestModel):
            @classmethod
            def get_to_many_relationship_config(cls) -> dict[str, str]:
                """Define many relations for error checking later"""

                return {f'test_{c}': c for c in ascii_lowercase}

        session_mock = _IntegrityErrorSession(_IntegrityErrorModel())
        db = DefaultDatabase(lambda: session_mock, [_IntegrityErrorModel])

        with pytest.raises(DataSourceError) as e:
            db.delete('test', 'does_not_matter')

        # some loose checks on the error...

        # title is correct looking
        assert 'integrity' in e.value.title.lower()
        # relationships are in there, for a hint
        assert ', '.join(ascii_lowercase) in e.value.detail

    def test_delete(self):
        """
        `DefaultDatabase().delete()` gets the right `Model` instance, and
        calls `delete()` on it.
        """

        model_mock = _TestModel()
        session_mock = _SessionMock(model_mock)
        db = DefaultDatabase(lambda: session_mock, [_TestModel])
        db.delete('test', 'why_should_I_care!')

        # same as get_by_id... 3 = query, filter, one_or_none, delete, commit
        assert len(session_mock.calls) == 5
        # query on correct table
        assert session_mock.calls[0] == ('query', (_TestModel,), {})
        # filter correct column
        assert session_mock.calls[1] == (
            'filter',
            (_TestModel.id == 'why_should_I_care!',),
            {}
        )
        # one_or_none
        assert session_mock.calls[2] == ('one_or_none', (), {})
        # delete
        assert session_mock.calls[3] == ('delete', (model_mock,), {})
        # finally -> commit
        assert session_mock.calls[4] == ('commit', (), {})
