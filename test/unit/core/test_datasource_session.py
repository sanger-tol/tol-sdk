# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

from tol.core import DataObject, DataSource, unsupported
from tol.core.datasource_session import DataSourceSession, _UpsertDict


class TestUpsertDict:
    def test_add_one_object(self):
        u_dict = _UpsertDict()
        d_object = DataObject(
            'test'
        )
        u_dict.add(d_object)

        assert len(u_dict.keys()) == 1
        assert u_dict['test'] == [d_object]

    def test_add_many_objects_one_type(self):
        u_dict = _UpsertDict()
        d_objects = [
            DataObject(
                'test',
                {
                    'field': f'value_{i}'
                }
            )
            for i in range(100)
        ]
        for d in d_objects:
            u_dict.add(d)
        
        assert len(u_dict.keys()) == 1
        assert u_dict['test'] == d_objects

    def test_add_one_object_for_many_types(self):
        u_dict = _UpsertDict()
        d_objects = [
            DataObject(
                f'test_{i}',
                {
                    'field': f'value_{i}'
                }
            )
            for i in range(100)
        ]
        for d in d_objects:
            u_dict.add(d)

        expected = {
            d.object_type: [d]
            for d in d_objects
        }

        assert dict(u_dict) == expected


class MockDataSource(DataSource):
    @unsupported()
    def get_by_id(self, object_type: str, *args, **kwargs):
        pass

    @unsupported()
    def get_list_page(self, object_type: str, *args, **kwargs):
        pass

    @unsupported()
    def upsert(self, object_type: str, *args, **kwargs):
        pass

    @unsupported()
    def get_list(self, object_type: str, *args, **kwargs):
        pass

    @unsupported()
    def multi_type_upsert(self, *args, **kwargs) -> None:
        pass


class TestDataSourceSession:
    def test_upsert_one_type(self):
        ds_upsert_mock = MagicMock()
        mock_data_source = type(
            '',
            (object,),
            {
                'upsert': ds_upsert_mock
            }
        )()
        objects = [
            DataObject('test', {'id': i})
            for i in range(100)
        ]
        sess = DataSourceSession(mock_data_source)
        sess.upsert(objects)
        sess.commit()
        expected = [('test', objects)]
        ds_upsert_mock.assert_called_once()
        observed = [
            args for (args, _) in ds_upsert_mock.call_args_list
        ]
        assert expected == observed

    def test_upsert_many_types(self):
        ds_upsert_mock = MagicMock()
        mock_data_source = type(
            '',
            (object,),
            {
                'upsert': ds_upsert_mock
            }
        )()
        objects = [
            DataObject(str(i), {'id': i, 'test': 'test'})
            for i in range(100)
        ]
        sess = DataSourceSession(mock_data_source)
        sess.upsert(objects)
        sess.commit()
        expected = [
            (obj.object_type, [obj])
            for obj in objects
        ]
        observed = [
            args for (args, _) in ds_upsert_mock.call_args_list
        ]
        assert expected == observed

    def test_multiple_upserts_multiple_types(self):
        ds_upsert_mock = MagicMock()
        mock_data_source = type(
            '',
            (object,),
            {
                'upsert': ds_upsert_mock
            }
        )()
        objects = [
            DataObject(str(i), {'id': i, 'test': 'test'})
            for i in range(100)
        ]
        sess = DataSourceSession(mock_data_source)
        # do two separate upserts with the same objects twice
        sess.upsert(objects)
        sess.upsert(reversed(objects))
        sess.commit()
        # should be treated as one
        expected = [
            (obj.object_type, [obj, obj])
            for obj in objects
        ]
        observed = [
            args for (args, _) in ds_upsert_mock.call_args_list
        ]
        assert expected == observed

    def test_context_manager(self):
        ds_upsert_mock = MagicMock()
        mock_data_source = type(
            '',
            (MockDataSource,),
            {
                'upsert': ds_upsert_mock
            }
        )({})
        objects = [
            DataObject(str(i), {'id': i, 'test': 'test'})
            for i in range(100)
        ]
        # do two separate upserts with the same objects twice
        with mock_data_source.session() as sess:
            sess.upsert(objects)
            sess.upsert(reversed(objects))
        # should have commited on leaving scope
        # should be treated as one
        expected = [
            (obj.object_type, [obj, obj])
            for obj in objects
        ]
        observed = [
            args for (args, _) in ds_upsert_mock.call_args_list
        ]
        assert expected == observed

    def test_mixed_iterable_types(self):
        ds_upsert_mock = MagicMock()
        mock_data_source = type(
            '',
            (MockDataSource,),
            {
                'upsert': ds_upsert_mock
            }
        )({})
        objects_list = [
            DataObject(str(i), {'id': i, 'test': 'test'})
            for i in range(100)
        ]
        objects_generator = (
            data_object for data_object in reversed(objects_list)
        )
        # do two separate upserts with the same objects twice
        with mock_data_source.session() as sess:
            sess.upsert(objects_generator)
            sess.upsert(objects_list)
        # should have commited on leaving scope
        # should be treated as one
        expected = [
            (obj.object_type, [obj, obj])
            for obj in reversed(objects_list)
        ]
        observed = [
            args for (args, _) in ds_upsert_mock.call_args_list
        ]
        assert expected == observed
