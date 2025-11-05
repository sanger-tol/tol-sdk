# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict
from unittest import TestCase
from unittest.mock import Mock

from tol.actions import UpsertAction
from tol.core import DataSource


class _MockDataSource(DataSource):
    """Empty DataSource for testing"""
    
    def upsert_batch(self, object_type: str, objects: Any) -> None:
        if object_type != 'test_type':
            raise ValueError("Unsupported object type")
        else:
            pass

    @property
    def supported_types(self):
        return ['non-relational']

    @property
    def attribute_types(self):
        return {
            'non-relational': {}
        }

class MockAction(UpsertAction):
    def __init__(self):
        super().__init__()

    def run(self,
            ids: list[str],
            datasource: DataSource,
            object_type: str,
            params: dict[str, Any] | None = None
        ) -> tuple[Dict[str, bool], int]:
        data_objects = self.__convert_to_data_objects(
            datasource=datasource,
            ids=ids,
            object_type=object_type,
            params=params
        )
        try:
            datasource.upsert_batch(object_type=object_type, objects=data_objects)
            return {'success': True}, 200
        except Exception as e:
            return {'error': str(e)}, 500
    
    def __convert_to_data_objects(self, datasource, ids, object_type, params = None):
        for id in ids:
            data_object = Mock()
            data_object.type_ = object_type
            data_object.id_ = id
            data_object.attributes = params
            yield data_object
    


class TestAction(TestCase):
    def test_run_success(self):
        action = MockAction()
        self.assertEqual(
            action.run(
                ids=['id1'],
                datasource=_MockDataSource({}),
                params=None,
                object_type='test_type'
            ),
            ({'success': True}, 200)
        )
    
    def test_run_failure(self):
        action = MockAction()
        self.assertEqual(
            action.run(
                ids=['id1'],
                datasource=_MockDataSource({}),
                params=None,
                object_type='invalid_type'
            ),
            ({'error': 'Unsupported object type'}, 500)
        )