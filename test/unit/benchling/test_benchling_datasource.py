# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase,
    mock
)

from benchling_sdk.errors import BenchlingError

from tol.benchling import BenchlingDataSource
from tol.benchling.benchling_converter import (
    CustomEntity,
    Folder,
    Location,
    Worklist
)
from tol.core import DataObject, core_data_object
from tol.core.data_object import ErrorObject


class MockBenchlingDataSource(BenchlingDataSource):
    def _get_benchling_interface(self, url, api_key):
        return mock.Mock()

    def _get_schemas(self, benchling_type: str):
        if benchling_type == 'custom_entity':
            return {
                'test_entity_type': {
                    '__id__': 'ts_DONTCARE',
                    'field_name': {
                        'name': 'Test Field',
                        'type': 'str',
                        'benchling_type': 'text',
                        'required': True,
                        'is_multi': False
                    },
                    'field_name2': {
                        'name': 'Test Field 2',
                        'type': 'int',
                        'benchling_type': 'integer',
                        'required': True,
                        'is_multi': False
                    }
                },
                'test_child_type': {
                    '__id__': 'ts_ANOTHER',
                    'parent': {
                        'name': 'Parent',
                        'type': 'str',
                        'benchling_type': 'entity_link',
                        'schema_id': 'ts_DONTCARE',
                        'required': True,
                        'is_multi': False

                    },
                    'name': {
                        'name': 'Name',
                        'type': 'str',
                        'benchling_type': 'text',
                        'required': True,
                        'is_multi': False
                    }
                }
            }
        elif benchling_type == 'location':
            return {
                'test_location_type': {
                    '__id__': 'ts_DONTCARE2',
                    'field_name': {
                        'name': 'Test Location Field',
                        'type': 'str',
                        'benchling_type': 'text',
                        'required': True,
                        'is_multi': False
                    },
                    'field_name2': {
                        'name': 'Test Location Field 2',
                        'type': 'int',
                        'benchling_type': 'integer',
                        'required': True,
                        'is_multi': False
                    }
                },
            }
        else:
            return {}


def mock_benchling_data_source() -> BenchlingDataSource:
    bds = MockBenchlingDataSource({
        'url': 'http://test/benchling',
        'api_key': '1234',
        'registry_id': '5678',
        'project_id': '6789',
        'folder_id': '8901'
    })
    core_data_object_mock = core_data_object(bds)
    return core_data_object_mock, bds


class TestBenchlingDataSource(TestCase):

    def test_attribute_types(self):
        _, bds = mock_benchling_data_source()
        expected = {
            'test_entity_type': {
                'field_name': 'str',
                'field_name2': 'int'
            },
            'test_child_type': {
                'name': 'str'
            },
            'test_location_type': {
                'field_name': 'str',
                'field_name2': 'int',
                'name': 'str',
                'barcode': 'str'
            },
            'folder': {
                'name': 'str'
            },
            'worklist': {
                'name': 'str',
                'worklist_type': 'str'
            },
            'worklist_item': {
                'name': 'str'
            },
            'transfer': {
                'source_entity_id': 'str',
                'destination_container_id': 'str'
            },
            'assay_result': {}
        }

        self.assertEqual(expected, bds.attribute_types)
        self.assertEqual(
            ['test_entity_type', 'test_child_type', 'test_location_type',
             'folder', 'worklist', 'worklist_item', 'transfer', 'assay_result'],
            bds.supported_types
        )

    def test_relationship_config(self):
        _, bds = mock_benchling_data_source()
        rc = bds.relationship_config
        self.assertEqual(
            {'parent': 'test_entity_type', 'folder': 'folder'},
            rc['test_child_type'].to_one
        )
        self.assertEqual({'folder': 'folder'}, rc['test_entity_type'].to_one)

    def test_get_by_id_custom_entity(self):
        _, bds = mock_benchling_data_source()
        obj = mock.create_autospec(CustomEntity, spec_set=True)
        obj.schema.name = 'test_entity_type'
        obj.id = '123'
        bds.benchling_interface.custom_entities.list.return_value = [[obj]]
        res = list(bds.get_by_ids('test_entity_type', ['123']))
        self.assertEqual(1, len(res))
        self.assertEqual('123', res[0].id)

    def test_get_by_id_worklist(self):
        _, bds = mock_benchling_data_source()
        obj = mock.create_autospec(Worklist, spec_set=True)
        obj.id = '123'
        obj.name = 'Worklist 1'
        bds.benchling_interface.v2.beta.worklists.list.return_value = [[obj]]
        res = list(bds.get_by_ids('worklist', ['123']))
        self.assertEqual(1, len(res))
        self.assertEqual('123', res[0].id)
        self.assertEqual('Worklist 1', res[0].name)

    def test_get_list_custom_entity(self):
        _, bds = mock_benchling_data_source()
        obj = mock.create_autospec(CustomEntity, spec_set=True)
        obj.schema.name = 'test_entity_type'
        obj.id = '123'
        bds.benchling_interface.custom_entities.list.return_value = [[obj]]
        res = list(bds.get_list('test_entity_type'))
        self.assertEqual(1, len(res))
        self.assertEqual('123', res[0].id)

    def test_get_list_worklist(self):
        _, bds = mock_benchling_data_source()
        obj = mock.create_autospec(Worklist, spec_set=True)
        obj.id = '123'
        obj.name = 'Worklist 1'
        bds.benchling_interface.v2.beta.worklists.list.return_value = [[obj]]
        res = list(bds.get_list('worklist'))
        self.assertEqual(1, len(res))
        self.assertEqual('123', res[0].id)
        self.assertEqual('Worklist 1', res[0].name)

    def test_get_list_folder(self):
        _, bds = mock_benchling_data_source()
        obj = mock.create_autospec(Folder, spec_set=True)
        obj.id = '123'
        obj.name = 'Folder 1'
        bds.benchling_interface.folders.list.return_value = [[obj]]
        res = list(bds.get_list('folder'))
        self.assertEqual(1, len(res))
        self.assertEqual('123', res[0].id)
        self.assertEqual('Folder 1', res[0].name)

    def test_get_list_location(self):
        _, bds = mock_benchling_data_source()
        obj = mock.create_autospec(Location, spec_set=True)
        obj.id = '123'
        obj.name = 'Location 1'
        obj.schema.name = 'test_location_type'
        obj.parent_storage_id = None
        bds.benchling_interface.locations.list.return_value = [[obj]]
        res = list(bds.get_list('test_location_type'))
        self.assertEqual(1, len(res))
        self.assertEqual('123', res[0].id)
        self.assertEqual('Location 1', res[0].name)

    def test_update_error(self):
        _, bds = mock_benchling_data_source()

        update1 = {'field_name': 'value1',
                   'field_name2': 2}
        update2 = {'field_name': 'value3',
                   'field_name2': 4}
        updates = [('123', update1),
                   ('456', update2)]
        status = mock.MagicMock()
        status.status = 'FAILED'
        bds.benchling_interface.tasks.wait_for_task.return_value = status
        # Error from trying singly
        bds.benchling_interface.custom_entities.update.side_effect = BenchlingError(
            status_code=400,
            headers={},
            json={'error': {'message': 'Boom'}},
            content='',
            parsed=''
        )

        res = bds.update('test_entity_type', updates)

        # properly formatted `ErrorObject` instances are returned
        assert len(res) == 2
        for obj in res:
            assert isinstance(obj, ErrorObject)
            assert obj.object_type == 'test_entity_type'

        # once for the page of 2, plus 2 single calls
        self.assertEqual(bds.benchling_interface.custom_entities.bulk_update.call_count, 1)
        self.assertEqual(bds.benchling_interface.custom_entities.update.call_count, 2)

    def test_insert_error(self):
        _, bds = mock_benchling_data_source()

        inserts = [
            self.__mock_obj(),
            self.__mock_obj()
        ]

        status = mock.MagicMock()
        status.status = 'FAILED'
        bds.benchling_interface.tasks.wait_for_task.return_value = status
        bds.benchling_interface.custom_entities.create.side_effect = BenchlingError(
            status_code=400,
            headers={},
            json={'error': {'message': 'Boom'}},
            content='',
            parsed=''
        )
        res = bds.insert('test_entity_type', inserts)

        # properly formatted `ErrorObject` instances are returned
        assert len(res) == 2
        for obj in res:
            assert isinstance(obj, ErrorObject)
            assert obj.object_type == 'test_entity_type'

        # once for the page of 2, plus 2 single calls
        self.assertEqual(bds.benchling_interface.custom_entities.bulk_create.call_count, 1)
        self.assertEqual(bds.benchling_interface.custom_entities.create.call_count, 2)

    def __mock_obj(self) -> DataObject:
        obj = mock.create_autospec(DataObject)
        obj.type = 'test_entity_type'
        obj.folder = None

        return obj
