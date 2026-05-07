# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from operator import eq
from string import ascii_lowercase
from typing import Any
from unittest.mock import MagicMock

import pytest

from sqlalchemy import Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import mapped_column

from tol.core import DataSourceError
from tol.sql.database import DefaultDatabase
from tol.sql.model import model_base


Base = model_base()


class _TestModel(Base):
    __tablename__ = 'test'

    id = mapped_column(Integer, primary_key=True)  # noqa: A003
    int_column = mapped_column(Integer)


class _OverrideIdModel(Base):
    __tablename__ = 'test_override'

    id_other = mapped_column(Integer, primary_key=True)

    def get_id_column_name():
        return 'id_other'


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

    def refresh(self, instance):
        return instance

    def flush(self, *args):
        pass

    def rollback(self):
        pass

    def filter(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('filter', args, kwargs))
        return self

    def execute(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('execute', args, kwargs))
        return self

    def scalars(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('scalars', args, kwargs))
        return self

    def unique(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('unique', args, kwargs))
        return self

    def delete(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('delete', args, kwargs))
        return self

    def commit(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('commit', args, kwargs))
        return self

    def one(self, *args, **kwargs) -> _SessionMock:  # noqa
        self.__calls.append(('one', args, kwargs))
        return self.__return_value

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
        return self.__return_value


class TestDefaultDatabase:
    def test_get_by_id_not_found(self):
        """get_by_id() gets a non-existent row -> return None"""

        session_mock = _SessionMock(None)
        db = DefaultDatabase(lambda: session_mock, [_TestModel])
        result = db.get_by_id('test', '404', session_mock)
        assert result is None

        # 2 = 1 scalars + 1 one_or_none
        assert len(session_mock.calls) == 2
        call, (select,), kwargs = session_mock.calls[0]
        assert call == 'scalars'

        # query on correct table
        assert [x.name for x in select.get_final_froms()] == ['test']
        assert kwargs == {}

        # finally one_or_none
        assert session_mock.calls[1] == ('one_or_none', (), {})

    def test_get_by_id_exists(self):
        """get_by_id() gets an existing row -> return it"""

        expected = _TestModel(
            id='302'
        )
        session_mock = _SessionMock(expected)
        db = DefaultDatabase(lambda: session_mock, [_TestModel])
        result = db.get_by_id('test', '302', session_mock)
        assert result == expected

        # 2 = 1 scalars + 1 one_or_none
        assert len(session_mock.calls) == 2
        call, (select,), kwargs = session_mock.calls[0]
        assert call == 'scalars'

        # query on correct table
        assert [x.name for x in select.get_final_froms()] == ['test']

        # correct column filter
        op = select.whereclause
        assert [op.left.name, op.operator, op.right.value] == ['id', eq, '302']
        assert kwargs == {}

        # finally one_or_none
        assert session_mock.calls[1] == ('one_or_none', (), {})

    def test_get_by_non_standard_id_column(self):
        """get_by_id using a different id_column"""

        expected = _OverrideIdModel(id_other='302')
        session_mock = _SessionMock(expected)
        db = DefaultDatabase(lambda: session_mock, [_OverrideIdModel])
        result = db.get_by_id('test_override', '302', session_mock)
        assert result == expected

        # 2 = 1 scalars + 1 one_or_none
        assert len(session_mock.calls) == 2
        call, (select,), kwargs = session_mock.calls[0]
        assert call == 'scalars'

        # query on correct table
        assert [x.name for x in select.get_final_froms()] == ['test_override']

        # correct column filter
        op = select.whereclause
        assert [op.left.name, op.operator, op.right.value] == ['id_other', eq, '302']
        assert kwargs == {}

        # finally one_or_none
        assert session_mock.calls[1] == ('one_or_none', (), {})

    def test_get_list_page_none_found(self):
        """get_list_page that returns no results at all, no filters"""

        session_mock = _SessionMock([])
        db = DefaultDatabase(lambda: session_mock, [_TestModel])
        result = db.get_page(
            'test',
            session_mock,
            offset=300,
            limit=100
        )
        assert list(result) == []

        # 3 = scalars + unique + all
        assert len(session_mock.calls) == 3
        call, (select,), kwargs = session_mock.calls[0]
        assert call == 'scalars'

        # query on correct table
        assert [x.name for x in select.get_final_froms()] == ['test']

        # correct offset and limit
        assert select._offset == 300
        assert select._limit == 100

        assert session_mock.calls[1] == ('unique', (), {})

        # finally all()
        assert session_mock.calls[2] == ('all', (), {})

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
            session_mock,
            offset=300,
            limit=100
        )
        assert list(result) == expected

        # 3 = scalars + unique + all
        assert len(session_mock.calls) == 3
        call, (select,), kwargs = session_mock.calls[0]
        assert call == 'scalars'

        # query on correct table
        assert [x.name for x in select.get_final_froms()] == ['test']

        # correct offset and limit
        assert select._offset == 300
        assert select._limit == 100

        assert session_mock.calls[1] == ('unique', (), {})

        # finally all()
        assert session_mock.calls[2] == ('all', (), {})

    def test_count_no_results(self):
        """count() works with no results (no filters) -> returns 0"""

        session_mock = _SessionMock((0,))
        db = DefaultDatabase(lambda: session_mock, [_TestModel])
        result = db.count('test', session_mock)
        assert result == 0

        # 2 = query + count
        assert len(session_mock.calls) == 2
        call, (select,), kwargs = session_mock.calls[0]
        assert call == 'execute'

        # query on correct table
        # assert [x.name for x in select.get_final_froms()] == ['test']
        table_names = []
        for x in select.get_final_froms():
            for y in x.element.get_final_froms():
                table_names.append(y.name)
        assert table_names == ['test']

        # then one
        assert session_mock.calls[1] == ('one', (), {})

    def test_count_results_found(self):
        """count() works with some results found (no filters)"""

        expected = (234,)
        session_mock = _SessionMock(expected)
        db = DefaultDatabase(lambda: session_mock, [_TestModel])
        result = db.count('test', session_mock)
        assert result == 234

        # 2 = query + count
        assert len(session_mock.calls) == 2
        call, (select,), kwargs = session_mock.calls[0]
        assert call == 'execute'

        # query on correct table
        # assert [x.name for x in select.get_final_froms()] == ['test']
        table_names = []
        for x in select.get_final_froms():
            for y in x.element.get_final_froms():
                table_names.append(y.name)
        assert table_names == ['test']

        # then one
        assert session_mock.calls[1] == ('one', (), {})

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
            db.delete('test', 'does_not_matter', session_mock)

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
        db.delete('test', 'why_should_I_care!', session_mock)

        # 4 = scalars, one_or_none, delete, commit
        assert len(session_mock.calls) == 4

        # query on correct table
        call, (select,), kwargs = session_mock.calls[0]
        assert call == 'scalars'
        assert [x.name for x in select.get_final_froms()] == ['test']

        # correct column filter
        op = select.whereclause
        assert [op.left.name, op.operator, op.right.value] == ['id', eq, 'why_should_I_care!']
        assert kwargs == {}

        # one_or_none
        assert session_mock.calls[1] == ('one_or_none', (), {})
        # delete
        assert session_mock.calls[2] == ('delete', (model_mock,), {})
        # finally -> commit
        assert session_mock.calls[3] == ('commit', (), {})

    def test_attribute_types(self):
        """
        the `attribute_types` property inspects the models with caching
        """

        model_a = MagicMock()
        model_a.get_attribute_types.return_value = {
            'string_column': str,
            'int_column': int
        }
        model_a.get_table_name.return_value = 'A'

        model_b = MagicMock()
        model_b.get_attribute_types.return_value = {
            'string_column': str,
            'bool_column': bool
        }
        model_b.get_table_name.return_value = 'B'

        db = DefaultDatabase(
            MagicMock(),
            [model_a, model_b]
        )

        # both mocks only called once
        model_a.get_attribute_types.assert_called_once()
        model_b.get_attribute_types.assert_called_once()

        expected = {
            'A': {
                'string_column': str,
                'int_column': int
            },
            'B': {
                'string_column': str,
                'bool_column': bool
            }
        }
        observed = db.attribute_types

        assert observed == expected

        # fetch again for good measure
        for _ in range(3):
            db.attribute_types

        # both mocks still only called once
        model_a.get_attribute_types.assert_called_once()
        model_b.get_attribute_types.assert_called_once()
