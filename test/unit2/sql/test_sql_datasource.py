# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional
from unittest.mock import MagicMock

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tol.core import DataSourceFilter, core_data_object
from tol.sql import SqlDataSource
from tol.sql.converter import Converter, TypeFunction
from tol.sql.database import Database
from tol.sql.filter import DatabaseFilter
from tol.sql.model import Model, model_base


class _MockDataObject:

    def __init__(self, type_, id_, attrs) -> None:
        self.__id = id_
        self.__type = type_
        self.__attrs = attrs

    @property
    def id(self):  # noqa A007
        return self.__id

    @property
    def type(self): # noqa A007
        return self.__type

    @property
    def attributes(self):
        return self.__attrs


class _MockBasicConverter(Converter):
    def __init__(self, type_function: TypeFunction) -> None:
        self.__type_function = type_function

    def convert(self, models: Iterable[Model]):
        return (
            _MockDataObject(
                type_=self.__type_function(m),
                id_=m.instance_id,
                attrs=m.instance_attributes
            ) if m is not None else None
            for m in models
        )


class _MockIdentityConverter:
    """Just returns the given iterable"""
    def convert(self, models):
        return models


ToOneBase = model_base()  # noqa


class Source(ToOneBase):
    __tablename__ = 'test'

    id: Mapped[str] = mapped_column(primary_key=True)
    target_key: Mapped[str] = mapped_column(
        ForeignKey('target.funny_id_lol')
    )
    a_target_on_my_back: Mapped['Target'] = relationship(
        back_populates='targets'
    )


class Target(ToOneBase):
    __tablename__ = 'target'

    funny_id_lol: Mapped[str] = mapped_column(primary_key=True)
    targets: Mapped['Source'] = relationship(
        back_populates='a_target_on_my_back'
    )


class TestSqlDataSource:
    def test_supported_types(self):
        """Render correctly from model_dict"""

        ds = SqlDataSource(
            None,
            {
                'easy': 'test',
                'A': 'test',
                'B': 'test',
                'C': 'test'
            },
            MagicMock(),
            None,
            MagicMock(),
            MagicMock()
        )
        assert ds.supported_types == ['easy', 'A', 'B', 'C']

    def test_get_by_id(self):
        """get_by_id without a database. One found, one not"""

        class _MockModel(Model):

            @classmethod
            def get_table_name(cls) -> str:
                return 'test'

            @classmethod
            def get_id_column_name(cls) -> str:
                return 'id'

            @property
            def instance_id(self) -> Optional[str]:
                return '302'

            @classmethod
            def get_column(cls, name: str):
                pass

            @property
            def instance_attributes(self) -> Dict[str, Any]:
                return {
                    'hype': 'Train',
                    'yes': True
                }

            @classmethod
            def get_to_many_relationship_config(cls):
                pass

            @classmethod
            def get_to_one_relationship_config(cls):
                pass

        class _SingleRowDatabase(Database):
            def get_by_id(self, tablename: str, id_: Any) -> Optional[Model]:
                return _MockModel() if id_ != '404' else None

            def get_list(self, *args):
                raise NotImplementedError()

            def count(self, tablename: str, filters: Optional[DataSourceFilter]) -> int:
                raise NotImplementedError()

        ds = SqlDataSource(
            _SingleRowDatabase(),
            {'tests': 'test'},
            MagicMock(),
            lambda _: _MockBasicConverter(lambda m: f'{m.get_table_name()}s'),
            MagicMock(),
            MagicMock()

        )
        core_data_object(ds)

        data_objects = list(ds.get_by_id('tests', ['302', '404']))
        assert len(data_objects) == 2

        data_object = data_objects[0]
        assert data_object.id == '302'
        assert data_object.type == 'tests'
        assert data_object.attributes == {
            'hype': 'Train',
            'yes': True
        }

        assert data_objects[1] is None

    def test_get_list_page(self):
        """get_list_page without a database"""

        class _MockModel(Model):
            def __init__(self, instance_id: str, attrs: Dict[str, Any]) -> None:
                self.__instance_id = instance_id
                self.__attrs = attrs

            @classmethod
            def get_table_name(cls) -> str:
                return 'test'

            @classmethod
            def get_id_column_name(cls) -> str:
                return 'id'

            @classmethod
            def get_column(cls, name: str):
                pass

            @classmethod
            def get_to_many_relationship_config(cls):
                pass

            @classmethod
            def get_to_one_relationship_config(cls):
                pass

            @property
            def instance_id(self) -> Optional[str]:
                return self.__instance_id

            @property
            def instance_attributes(self) -> Dict[str, Any]:
                return self.__attrs

        class _AutoIncrementDatabase(Database):
            def get_by_id(self, tablename: str, id_: Any) -> Optional[Model]:
                raise NotImplementedError()

            def get_list(
                self,
                tablename: str,
                filters: Optional[DataSourceFilter] = None,
                sort_by: Optional[str] = None,
                offset: Optional[int] = None,
                limit: Optional[int] = None
            ) -> Iterable[Model]:

                return (
                    _MockModel(str(i), {'hype': f'{"A" * i} train'})
                    for i in range(offset, offset + limit)
                )

            def count(
                self,
                tablename: str,
                filters: Optional[DataSourceFilter] = None
            ) -> int:
                return 10001

        ds = SqlDataSource(
            _AutoIncrementDatabase(),
            {'tests': 'test'},
            MagicMock(),
            lambda _: _MockBasicConverter(lambda m: f'{m.get_table_name()}s'),
            MagicMock(),
            MagicMock()
        )
        core_data_object(ds)

        data_objects, count = ds.get_list_page(
            'tests',
            10,
            page_size=30
        )
        data_objects = list(data_objects)

        assert count == 10001
        assert len(data_objects) == 30

        for i, data_object in enumerate(data_objects, start=270):  # 270=30*(10-1)
            assert data_object.id == str(i)
            assert data_object.type == 'tests'
            assert data_object.attributes == {
                'hype': f'{"A" * i} train'
            }

    def test_get_list(self):
        """uses (and hides) paged Database().get_list() behind the scenes"""

        stop = 456
        """The number of results to return"""

        class _MockDatabase:
            def __init__(self) -> None:
                self.__get_count = 0

            @property
            def get_count(self) -> int:
                return self.__get_count

            def get_list(
                self,
                tablename: str,
                filters: Optional[DatabaseFilter] = None,
                sort_by: Optional[str] = None,
                offset: Optional[int] = None,
                limit: Optional[int] = None
            ):
                # increment the get count
                self.__get_count += 1

                # return a sequence of numbers
                if offset + limit > stop:
                    return range(offset, stop)
                else:
                    return range(offset, offset + limit)

        mock_db = _MockDatabase()

        ds = SqlDataSource(
            mock_db,
            {'tests': 'test'},
            MagicMock(),
            lambda _: _MockIdentityConverter(),
            MagicMock(),
            MagicMock()
        )
        core_data_object(ds)

        page_size = ds.get_page_size()
        iterator = ds.get_list('tests')
        count = 0
        for i in range(stop // page_size):
            # assert that a page transition has occured
            assert mock_db.get_count == i
            for _ in range(page_size):
                # assert that the number is right
                assert next(iterator) == count
                count += 1

    def test_get_list_eventually_terminates(self):
        """get_list must eventually stop"""

        class _MockDatabase:
            def __init__(self) -> None:
                self.__get_count = 0

            def get_list(
                self,
                tablename: str,
                filters: Optional[DatabaseFilter] = None,
                sort_by: Optional[str] = None,
                offset: Optional[int] = None,
                limit: Optional[int] = None
            ):
                if self.__get_count > 4:
                    return []
                else:
                    self.__get_count += 1
                    return range(offset, offset + limit)

        mock_db = _MockDatabase()

        ds = SqlDataSource(
            mock_db,
            {'tests': 'test'},
            MagicMock(),
            lambda _: _MockIdentityConverter(),
            MagicMock(),
            MagicMock()
        )
        core_data_object(ds)

        page_size = ds.get_page_size()
        list_models = list(ds.get_list('tests'))
        assert len(list_models) == page_size * 5

    def test_get_to_one_relation(self):
        """to_one_relation works when populated"""
        #TODO do

    def test_get_to_one_relation_none(self):
        """
        to_one_relation works when the relation foreign key is not populated
        """

        ds = SqlDataSource(
            MagicMock(),
            {'tests': 'test', 'targets': 'target'},
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock()
        )
        core_data_object(ds)

        Base = model_base()  # noqa
