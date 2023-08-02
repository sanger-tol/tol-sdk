# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import List
from unittest.mock import call

from sqlalchemy.orm import Mapped, mapped_column

from tol.sql.model import model_base
from tol.sql.sort import DefaultDatabaseSorter


class _MockModel:
    """Mocks a model, for sorting only"""

    class int_column:  # noqa N801
        @staticmethod
        def desc():
            return False

    class identifier_column:  # noqa N801
        @staticmethod
        def asc():
            return True

    @classmethod
    def get_column(cls, column_name):
        if column_name == 'int_column':
            return cls.int_column
        if column_name == 'identifier_column':
            return cls.identifier_column

    @classmethod
    def get_id_column_name(cls) -> str:
        return 'identifier_column'


class _MockIdModel(model_base()):
    """A mock model with default id"""

    __tablename__ = 'lol'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa


class _MockIdRenamedModel:
    """A mock model with renamed id"""

    class id_renamed:  # noqa N801
        @staticmethod
        def desc():
            return False

    @classmethod
    def get_column(cls, name):
        assert name == 'id_renamed'
        return cls.id_renamed

    @classmethod
    def get_id_column_name(cls) -> str:
        return 'id_renamed'


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
            call(_MockModel.int_column),
            call(_MockModel.identifier_column)
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
            call(_MockModel.int_column.desc()),
            call(_MockModel.identifier_column)
        ]

    def test_by_id(self):
        """
        Sorting by "id" with the default column is correct
        """

        sorter = DefaultDatabaseSorter('id')
        query = sorter.sort(
            MockQuery(),
            'test',
            {'test': _MockIdModel},
        )
        assert query.sort_calls == [
            call(_MockIdModel.id)
        ]

    def test_by_renamed_id(self):
        """
        Sorting by "id" with a renamed column is correct
        """

        sorter = DefaultDatabaseSorter('-id')
        query = sorter.sort(
            MockQuery(),
            'test',
            {'test': _MockIdRenamedModel},
        )
        # it hits id_renamed and not (the non-existent) id column
        assert query.sort_calls == [
            call(_MockIdRenamedModel.id_renamed.desc())
        ]
