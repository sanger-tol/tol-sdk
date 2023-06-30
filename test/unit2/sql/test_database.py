# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Optional
from unittest import mock

from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from sqlalchemy.orm import Mapped, mapped_column

from tol.sql.database import DefaultDatabase
from tol.sql.model import Model, model_base


BaseModel = model_base()


class _TestModel(BaseModel):

    __tablename__ = 'test'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa A003
    int_column: Mapped[int] = mapped_column()


class _eq_column:
    def __init__(self, name: str) -> None:
        self.__name = name

    def __eq__(self, __o: str) -> tuple[str, str, str]:
        return self.__name, '__eq__', __o


class Source(Model):

    id = _eq_column('id')
    target_key = _eq_column('target_key')

    @classmethod
    def get_column(cls, name: str):
        assert name in ['id', 'target_key']
        return getattr(cls, name)

    @classmethod
    def get_id_column_name(cls) -> str:
        return 'id'

    @classmethod
    def get_table_name(cls) -> str:
        return 'source'

    @classmethod
    def get_to_many_relationship_config(cls) -> dict[str, str]:
        return {}

    @classmethod
    def get_to_one_relationship_config(cls) -> dict[str, str]:
        return {
            'a_target_on_my_back': 'target'
        }

    @property
    def instance_attributes(self) -> dict[str, Any]:
        return {}

    @property
    def instance_id(self) -> Optional[str]:
        return None


class Target(Model):
    funny_id_lol = _eq_column('funny_id_lol')

    @classmethod
    def get_column(cls, name: str):
        assert name == 'funny_id_lol'
        return cls.funny_id_lol

    @classmethod
    def get_id_column_name(cls) -> str:
        'funny_id_lol'

    @classmethod
    def get_table_name(cls) -> str:
        return 'target'

    @classmethod
    def get_to_many_relationship_config(cls) -> dict[str, str]:
        return {
            'sources_my_own': 'source'
        }

    @classmethod
    def get_to_one_relationship_config(cls) -> dict[str, str]:
        return {}

    @property
    def instance_attributes(self) -> dict[str, Any]:
        return {}

    @property
    def instance_id(self) -> Optional[str]:
        return None

class TestDefaultDatabase:
    def test_get_by_id_not_found(self):
        """get_by_id() gets a non-existent row -> return None"""

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    # return no results for searching id == 404
                    [
                        mock.call.query(_TestModel),
                        mock.call.filter(_TestModel.id == '404')
                    ],
                    []
                ),
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_TestModel]
        )
        result = db.get_by_id('test', '404')
        assert result is None

    def test_get_by_id_exists(self):
        """get_by_id() gets an existing row -> return it"""

        expected = _TestModel(
            id='302'
        )

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(_TestModel),
                        mock.call.filter(_TestModel.id == '302')
                    ],
                    [expected]
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_TestModel]
        )
        result = db.get_by_id('test', '302')
        assert result == expected

    def test_get_by_non_standard_id_column(self):
        """get_by_id using a different id_column"""

        class _OverrideIdModel(BaseModel):

            __tablename__ = 'test_override'

            id_other: Mapped[str] = mapped_column(primary_key=True)

            @classmethod
            def get_id_column_name(cls) -> str:
                return 'id_other'

        expected = _OverrideIdModel(id_other='302')

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(_OverrideIdModel),
                        mock.call.filter(_OverrideIdModel.id_other == '302')
                    ],
                    [expected]
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_OverrideIdModel]
        )
        result = db.get_by_id('test_override', '302')
        assert result == expected

    def test_get_list_page_none_found(self):
        """get_list_page that returns no results at all, no filters"""

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(_TestModel),
                        mock.call.limit(100),
                        mock.call.offset(300)
                    ],
                    []
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_TestModel]
        )
        result = db.get_page(
            'test',
            offset=300,
            limit=100
        )
        assert list(result) == []

    def test_get_list_page_some(self):
        """get_list_page that does find some results, and returns them"""

        expected = [
            _TestModel(id=i)
            for i in range(300, 400)
        ]
        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(_TestModel),
                        mock.call.limit(100),
                        mock.call.offset(300)
                    ],
                    expected
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_TestModel]
        )
        result = db.get_page(
            'test',
            offset=300,
            limit=100
        )
        assert list(result) == expected

    def test_count_no_results(self):
        """count() works with no results (no filters) -> returns 0"""

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(_TestModel)
                    ],
                    []  # no results
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_TestModel]
        )
        result = db.count('test')
        assert result == 0

    def test_count_results_found(self):
        """count() works with some results found (no filters)"""

        expected = list(range(234))

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(_TestModel)
                    ],
                    expected
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [_TestModel]
        )
        result = db.count('test')
        assert result == 234

    def test_get_to_one_relation_not_found(self):
        """get_to_one_relation() when none is found"""

        source = Source(id='nada', target_key='link')

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                # getting the source
                (
                    [
                        mock.call.query(Source),
                        mock.call.filter(Source.id == 'nada')
                    ],
                    [source]
                ),
                # getting the target
                (
                    [
                        mock.call.query(Target),
                        mock.call.filter(
                            Target.funny_id_lol == 'link'
                        )
                    ],
                    []
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [Source, Target]
        )
        result = db.get_to_one_relation(
            'source',
            'nada',
            'a_target_on_my_back'
        )
        assert result is None

    def test_get_to_one_relation_one_found(self):
        """get_to_one_relation() when a result is found"""

        source = Source(id='nada', target_key='link')
        expected = Target(funny_id_lol='link')

        sqlalchemy_mock = UnifiedAlchemyMagicMock(
            data=[
                # getting the source
                (
                    [
                        mock.call.query(Source),
                        mock.call.filter(Source.id == 'nada')
                    ],
                    [source]
                ),
                # getting the target
                (
                    [
                        mock.call.query(Target),
                        mock.call.filter(
                            Target.funny_id_lol == 'link'
                        )
                    ],
                    [expected]
                )
            ]
        )
        db = DefaultDatabase(
            lambda: sqlalchemy_mock,
            [Source, Target]
        )
        result = db.get_to_one_relation(
            'source',
            'nada',
            'a_target_on_my_back'
        )
        assert result == expected
