# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase,
    mock
)

from tol.benchling import BenchlingDataSource
from tol.core import DataObject, core_data_object
from tol.core.data_object import ErrorObject


class MockBenchlingDataSource(BenchlingDataSource):
    def _get_benchling_interface(self, url, api_key):
        return mock.Mock()

    def _get_entity_schemas(self):
        return {
            'test_entity_type': {
                '__id__': 'ts_DONTCARE',
                'field_name': {
                    'name': 'Test Field',
                    'type': 'str'
                },
                'field_name2': {
                    'name': 'Test Field 2',
                    'type': 'int'
                }
            }
        }


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
            }
        }
        self.assertEqual(expected, bds.attribute_types)
        self.assertEqual(['test_entity_type'], bds.supported_types)

    def test_update(self):
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
        res = bds.update('test_entity_type', updates)

        # properly formatted `ErrorObject` instances are returned
        assert len(res) == 2
        for obj in res:
            assert isinstance(obj, ErrorObject)
            assert obj.object_type == 'test_entity_type'

        # once for the page of 2, plus once _each_ for both individually ( = 3)
        self.assertEqual(bds.benchling_interface.custom_entities.bulk_update.call_count, 3)

    def test_insert(self):
        _, bds = mock_benchling_data_source()

        inserts = [
            self.__mock_obj(),
            self.__mock_obj()
        ]

        status = mock.MagicMock()
        status.status = 'FAILED'
        bds.benchling_interface.tasks.wait_for_task.return_value = status
        res = bds.insert('test_entity_type', inserts)

        # properly formatted `ErrorObject` instances are returned
        assert len(res) == 2
        for obj in res:
            assert isinstance(obj, ErrorObject)
            assert obj.object_type == 'test_entity_type'

        # once for the page of 2, plus once _each_ for both individually ( = 3)
        self.assertEqual(bds.benchling_interface.custom_entities.bulk_create.call_count, 3)

    def __mock_obj(self) -> DataObject:
        obj = mock.create_autospec(DataObject, spec_set=True)
        obj.type = 'test_entity_type'

        return obj
