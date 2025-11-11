# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from string import ascii_uppercase
from typing import Any, Dict, Iterable, Optional
from unittest.mock import MagicMock, Mock, PropertyMock, call, create_autospec

from sqlalchemy.orm import Session

from tol.core import DataObject, DataSourceFilter, core_data_object
from tol.sql import SqlDataSource, create_sql_datasource
from tol.sql.database import Database
from tol.sql.filter import DatabaseFilter
from tol.sql.model import Model
from tol.sql.sql_converter import Converter, TypeFunction


class _MockDataObject:

    def __init__(self, type_, id_, attrs) -> None:
        self.__id = id_
        self.__type = type_
        self.__attrs = attrs

    @property
    def id(self):  # noqa A007
        return self.__id

    @property
    def type(self):  # noqa A007
        return self.__type

    @property
    def attributes(self):
        return self.__attrs


class _MockIdentityConverter(Converter):
    """Just returns the given iterable"""

    def convert(self, m):
        return m


class _MockBasicConverter(Converter):
    def __init__(self, type_function: TypeFunction) -> None:
        self.__type_function = type_function

    def convert(self, m: Model) -> _MockDataObject:
        return _MockDataObject(
            type_=self.__type_function(m),
            id_=m.instance_id,
            attrs=m.instance_attributes
        )


class _MockPrefixConverter(Converter):
    """Converts to string and adds a prefix for each "Model"."""

    def __init__(self, prefix: str) -> None:
        self.__prefix = prefix

    def convert(self, m: Any) -> str:
        assert m is not None
        return f'{self.__prefix}{m}'


class TestSqlDataSource:
    def test_supported_types(self):
        """Render correctly from model_dict"""

        test_db = MagicMock()
        type(test_db).attribute_types = PropertyMock(
            return_value={}
        )

        ds = SqlDataSource(
            test_db,
            {
                'easy': 'test',
                'A': 'test',
                'B': 'test',
                'C': 'test'
            },
            MagicMock(),
            None,
            MagicMock(),
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

            @classmethod
            def get_attribute_types(cls) -> dict[str, type]:
                raise NotImplementedError()

            @classmethod
            def get_attribute_types_including_id(cls) -> dict[str, type]:
                raise NotImplementedError()

            @property
            def instance_to_one_relations(self) -> dict[str, Optional[Model]]:
                pass

            @property
            def instance_to_many_relations(self) -> dict[str, Iterable[Model]]:
                pass

            @classmethod
            def get_foreign_key_name(cls, relationship_name: str) -> str:
                raise NotImplementedError()

        class _SingleRowDatabase:
            def get_by_id(self, tablename: str, id_: Any, *args, **kwargs) -> Optional[Model]:
                return _MockModel() if id_ != '404' else None

            @property
            def attribute_types(self):
                return {}

            @property
            def attribute_types_including_id(self):
                return {}

            @property
            def session_factory(self):
                return MagicMock()

            def build_requests_tree(self, *args):
                return Mock()

        ds = SqlDataSource(
            _SingleRowDatabase(),
            {'tests': 'test'},
            MagicMock(),
            lambda *_: _MockBasicConverter(lambda m: f'{m.get_table_name()}s'),
            MagicMock(),
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

            @classmethod
            def get_foreign_key_name(cls, relationship_name: str) -> str:
                raise NotImplementedError()

            @classmethod
            def get_attribute_types(cls) -> dict[str, type]:
                raise NotImplementedError()

            @property
            def instance_id(self) -> Optional[str]:
                return self.__instance_id

            @property
            def instance_attributes(self) -> Dict[str, Any]:
                return self.__attrs

            @property
            def instance_to_one_relations(self) -> dict[str, Optional[Model]]:
                pass

            @property
            def instance_to_many_relations(self) -> dict[str, Iterable[Model]]:
                pass

        class _AutoIncrementDatabase:
            def get_page(
                self,
                tablename: str,
                in_session,
                filters: Optional[DataSourceFilter] = None,
                sort_by: Optional[str] = None,
                offset: Optional[int] = None,
                limit: Optional[int] = None,
                **kwargs
            ) -> Iterable[Model]:

                return (
                    _MockModel(str(i), {'hype': f'{"A" * i} train'})
                    for i in range(offset, offset + limit)
                )

            @property
            def session_factory(self):
                return MagicMock()

            @property
            def attribute_types(self):
                return {}

            @property
            def attribute_types_including_id(self):
                return {}

            def build_requests_tree(self, *args):
                return Mock()

            def count(
                self,
                tablename: str,
                in_session,
                filters: Optional[DataSourceFilter] = None,
                **kwargs
            ) -> int:
                return 10001

        ds = SqlDataSource(
            _AutoIncrementDatabase(),
            {'tests': 'test'},
            MagicMock(),
            lambda *_: _MockBasicConverter(lambda m: f'{m.get_table_name()}s'),
            MagicMock(),
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

    def test_get_count(self):
        """uses Database().count() behind the scenes"""

        class _MockDatabase:
            def __init__(self) -> None:
                self.__get_count = 123

            @property
            def attribute_types(self):
                return {}

            @property
            def attribute_types_including_id(self):
                return {}

            def count(
                self,
                tablename: str,
                in_session,
                filters: Optional[DatabaseFilter] = None,
                **kwargs
            ) -> int:
                return self.__get_count

            @property
            def session_factory(self):
                return MagicMock()

        mock_db = _MockDatabase()

        ds = SqlDataSource(
            mock_db,
            {'tests': 'test'},
            MagicMock(),
            lambda *_: _MockIdentityConverter(),
            MagicMock(),
            MagicMock(),
            MagicMock()
        )
        core_data_object(ds)

        cnt = ds.get_count('tests')
        assert cnt == 123

    def test_get_to_one_relation_none(self):
        """no to-one relation of given key -> return None"""

        class _MockDatabase:
            def get_to_one_relation(self, *args, **kwargs):
                return None

            @property
            def attribute_types(self):
                return {}

            @property
            def attribute_types_including_id(self):
                return {}

            @property
            def session_factory(self):
                return MagicMock()

        mock_db = _MockDatabase()

        ds = SqlDataSource(
            mock_db,
            {'tests': 'test'},
            MagicMock(),
            lambda *_: _MockIdentityConverter(),
            MagicMock(),
            MagicMock(),
            MagicMock()
        )
        ds.data_object_factory = lambda *_: None

        mock_object = self.__get_mock_data_object('tests', 'lol')

        one_relation = ds.get_to_one_relation(
            mock_object,
            'no_matter'
        )

        assert one_relation is None

    def test_get_to_one_relation_found(self):
        """relation of given key exists -> convert and return"""

        class _MockDatabase:
            def get_to_one_relation(self, *args, **kwargs):
                return 'I found one!!!!'

            @property
            def attribute_types_including_id(self):
                return {}

            @property
            def attribute_types(self):
                return {}

            @property
            def session_factory(self):
                return MagicMock()

        mock_db = _MockDatabase()

        ds = SqlDataSource(
            mock_db,
            {'tests': 'test'},
            MagicMock(),
            lambda *_: _MockPrefixConverter('look... '),
            MagicMock(),
            MagicMock(),
            MagicMock()
        )
        ds.data_object_factory = lambda *_: None

        mock_object = self.__get_mock_data_object('tests', 'lol')

        one_relation = ds.get_to_one_relation(
            mock_object,
            'no_matter'
        )
        # result is concatenated with prefix
        assert one_relation == 'look... I found one!!!!'

    def test_get_to_many_relations_empty(self):
        """no to-many relations of given key -> return empty"""

        class _MockDatabase:

            @property
            def session_factory(self):
                return MagicMock()

            def get_to_many_relations(
                self,
                tablename: str,
                instance_id: str,
                relationship_name: str,
                in_session,
                **kwargs
            ):
                assert tablename == 'test'
                assert instance_id == 'lol'
                assert relationship_name == 'no_matter'
                return []

            @property
            def attribute_types(self):
                return {}

            @property
            def attribute_types_including_id(self):
                return {}

        mock_db = _MockDatabase()

        ds = SqlDataSource(
            mock_db,
            {'tests': 'test'},
            MagicMock(),
            lambda *_: _MockPrefixConverter('look... '),
            MagicMock(),
            MagicMock(),
            MagicMock()
        )
        ds.data_object_factory = lambda *_: None

        mock_object = self.__get_mock_data_object('tests', 'lol')

        many_relations = ds.get_to_many_relations(
            mock_object,
            'no_matter'
        )
        assert list(many_relations) == []

    def test_get_to_many_relations_found(self):
        """relations of given key exist -> convert and return"""

        prefix = 'hyped_up-'
        inputs = [str(i) for i in range(2, 99, 4)]
        expected = [f'{prefix}{i}' for i in inputs]

        class _MockDatabase:
            def get_to_many_relations(
                self,
                tablename: str,
                instance_id: str,
                relationship_name: str,
                in_session,
                **kwargs
            ):
                assert tablename == 'test'
                assert instance_id == 'lol'
                assert relationship_name == 'no_matter'

                return inputs

            @property
            def session_factory(self):
                return MagicMock()

            @property
            def attribute_types(self):
                return {}

            @property
            def attribute_types_including_id(self):
                return {}

        mock_db = _MockDatabase()

        ds = SqlDataSource(
            mock_db,
            {'tests': 'test'},
            MagicMock(),
            lambda *_: _MockPrefixConverter(prefix),
            MagicMock(),
            MagicMock(),
            MagicMock()
        )
        ds.data_object_factory = lambda *_: None

        mock_object = self.__get_mock_data_object('tests', 'lol')

        many_relations = ds.get_to_many_relations(
            mock_object,
            'no_matter'
        )
        assert list(many_relations) == expected

    def test_delete(self):
        """
        `SqlDataSource().delete()` calls `Database().delete()` correctly
        """

        mock_sess = create_autospec(Session)

        mock_sess_factory = MagicMock()
        mock_sess_factory.return_value = mock_sess

        mock_db = MagicMock()
        mock_db.session_factory = mock_sess_factory

        ds = SqlDataSource(
            mock_db,
            {'tests': 'mapped_tablename'},
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock()
        )
        ds.delete('tests', list(ascii_uppercase))

        assert mock_db.delete.call_args_list == [
            call('mapped_tablename', c, mock_sess, user_id=None) for c in ascii_uppercase
        ]

    def test_upsert(self):
        """
        `SqlDataSource().upsert()` calls `Database().upsert()` and
        `BackConverter().convert() correctly`
        """

        mock_sess = create_autospec(Session)

        mock_sess_factory = MagicMock()
        mock_sess_factory.return_value = mock_sess

        mock_db = MagicMock()
        mock_db.session_factory = mock_sess_factory

        mock_model = MagicMock()
        mock_model.get_table_name.return_value = 'test'
        mock_back_converter = MagicMock()
        mock_back_converter.convert_iterable.return_value = [mock_model]
        mock_object = self.__get_mock_data_object('tests', 'lol')
        ds = SqlDataSource(
            mock_db,
            {'tests': 'mapped_tablename'},
            MagicMock(),
            MagicMock(),
            lambda: mock_back_converter,
            MagicMock(),
            MagicMock(),
        )
        ds.data_object_factory = MagicMock()
        ds.upsert('tests', [mock_object])
        mock_db.upsert.assert_called_once_with(
            mock_model,
            mock_sess,
            user_id=None,
            merge_collections=None,
        )

    def test_get_attribute_types(self):
        """
        `SqlDataSource().get_attribute_types()` uses a cached fetch of
        `Database().attribute_types`.
        """

        mock_db = MagicMock()
        mock_attribute_types = PropertyMock(
            return_value={
                'A': {
                    'test': int
                },
                'B': {
                    'test_string': str,
                    'boolean': bool
                }
            }
        )
        type(mock_db).attribute_types_including_id = mock_attribute_types

        ds = SqlDataSource(
            mock_db,
            {'a': 'A', 'b': 'B'},
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock()
        )

        # called once on instantiaton, never again
        mock_attribute_types.assert_called_once()

        # get 'a', still only called once
        assert ds.get_attribute_types('a') == {'test': 'int'}
        mock_attribute_types.assert_called_once()

        # get 'b', still only called once
        assert ds.get_attribute_types('b') == {
            'test_string': 'str',
            'boolean': 'bool'
        }
        mock_attribute_types.assert_called_once()

    def test_user_id_delete(self):
        """user_id is set on delete"""

        mock_sess = create_autospec(Session)

        mock_sess_factory = MagicMock()
        mock_sess_factory.return_value = mock_sess

        mock_db = MagicMock()
        mock_db.session_factory = mock_sess_factory
        type(mock_db).attribute_types = PropertyMock(
            return_value={'test': {}}
        )

        mock_model = Mock()
        mock_model.get_table_name.return_value = 'test'
        mock_model.get_to_one_relationship_config.return_value = {}
        mock_model.get_to_many_relationship_config.return_value = {}

        sql_ds = create_sql_datasource(
            [mock_model],
            '',
            behind_api=True,
            api_user_id_getter=lambda: 'a user ID',
            database_factory=lambda __a, __b: mock_db
        )

        sql_ds.delete('test', ['test_ID'])

        mock_db.delete.assert_called_once_with(
            'test',
            'test_ID',
            mock_sess,
            user_id='a user ID'
        )

    def test_user_id_upsert(self):
        """user_id is set on upsert"""

        mock_sess = create_autospec(Session)

        mock_sess_factory = MagicMock()
        mock_sess_factory.return_value = mock_sess

        mock_db = MagicMock()
        mock_db.session_factory = mock_sess_factory
        type(mock_db).attribute_types = PropertyMock(
            return_value={'test': {}}
        )

        mock_model = Mock()
        mock_model.get_table_name.return_value = 'test'
        mock_model.get_to_one_relationship_config.return_value = {}
        mock_model.get_to_many_relationship_config.return_value = {}

        mock_model_instance = Mock()
        mock_model_factory = Mock()
        mock_model_factory.convert_iterable.return_value = [mock_model_instance]

        sql_ds = create_sql_datasource(
            [mock_model],
            '',
            behind_api=True,
            api_user_id_getter=lambda: 'a user ID',
            database_factory=lambda __a, __b: mock_db,
            model_factory=lambda __a, __b: lambda: mock_model_factory
        )
        sql_ds.data_object_factory = Mock()

        mock_obj = self.__get_mock_data_object('test', '1')

        sql_ds.upsert('test', [mock_obj])

        mock_db.upsert.assert_called_once_with(
            mock_model_instance,
            mock_sess,
            user_id='a user ID',
            merge_collections=None,
        )

    def test_insert(self):
        """`SqlDataSource().insert()`"""

        mock_sess = create_autospec(Session)

        mock_db = create_autospec(Database, spec_set=True)
        mock_db.attribute_types = {'test': {}}
        mock_db.attribute_types_including_id = {'test': {}}
        mock_db.session_factory.return_value = mock_sess

        mock_model = create_autospec(Model, spec_set=True)
        mock_model.get_table_name.return_value = 'test'
        mock_model.get_to_one_relationship_config.return_value = {}
        mock_model.get_to_many_relationship_config.return_value = {}

        mock_model_factory = Mock()
        mock_model_factory.convert_iterable.side_effect = lambda a: a

        sql_ds = create_sql_datasource(
            [mock_model],
            '',
            behind_api=True,
            api_user_id_getter=lambda: 'a user ID',
            database_factory=lambda __a, __b: mock_db,
            model_factory=lambda __a, __b: lambda: mock_model_factory
        )
        sql_ds.data_object_factory = Mock()

        mock_objects = [
            create_autospec(DataObject, spec_set=True)
            for _ in range(3)
        ]

        sql_ds.insert('test', mock_objects)

        mock_model_factory.convert_iterable.assert_called_once()

        expected_insert_calls = [
            call(obj, mock_sess, user_id='a user ID')
            for obj in mock_objects
        ]
        assert mock_db.insert.call_args_list == expected_insert_calls

    def __get_mock_data_object(self, type_: str, id_: str) -> MagicMock:
        """Mocks a DataObject of given type and id"""

        object_mock = MagicMock()
        type(object_mock).type = PropertyMock(return_value=type_)
        type(object_mock).id = PropertyMock(return_value=id_)

        return object_mock
