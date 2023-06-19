# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, Iterable, Optional

from tol.core import DataSourceFilter
from tol.sql import SqlDataSource
from tol.sql.database import Database
from tol.sql.model import Model


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
            }
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

        class _SingleRowDatabase(Database):
            def get_by_id(self, tablename: str, id_: Any) -> Optional[Model]:
                return _MockModel() if id_ != '404' else None

            def get_list(self, *args):
                raise NotImplementedError()

            def count(self, tablename: str, filters: Optional[DataSourceFilter]) -> int:
                raise NotImplementedError()

        ds = SqlDataSource(_SingleRowDatabase(), {'tests': 'test'})

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

    def test_get_list(self):
        """get_list without a database"""

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

            @property
            def instance_id(self) -> Optional[str]:
                return self.__instance_id

            @classmethod
            def get_column(cls, name: str):
                pass

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
                    for i in range(99)
                )

            def count(self, tablename: str, filters: Optional[DataSourceFilter]) -> int:
                raise NotImplementedError()

        ds = SqlDataSource(_AutoIncrementDatabase(), {'tests': 'test'})

        data_objects = list(ds.get_list('tests'))
        assert len(data_objects) == 99

        for i, data_object in enumerate(data_objects):
            assert data_object.id == str(i)
            assert data_object.type == 'tests'
            assert data_object.attributes == {
                'hype': f'{"A" * i} train'
            }

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

        ds = SqlDataSource(_AutoIncrementDatabase(), {'tests': 'test'})

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
