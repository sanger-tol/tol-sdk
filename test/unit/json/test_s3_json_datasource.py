# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import (
    TestCase
)

from tol.core import (
    core_data_object
)
from tol.json import (
    S3JsonDataSource
)

class MockS3JsonDataSource(S3JsonDataSource):
    def _load_json_from_s3(self, s3_bucket, s3_object):
        return [
            {
                'Id': 1,
                'Value': 'Value 1',
                'Optional': 'YES',
                'Boolean': True,
                'Float': 2.34,
                'Datetime': datetime(2024, 1, 1, 12, 13, 14).isoformat()
            },
            {
                'Id': 2,
                'Value': 'Value 2',
                'Optional': None,
                'Boolean': False,
                'Float': None,
                'Datetime': None
            },
            {
                'Id': 3,
                'Value': 'Value 3',
                'Optional': 'NO',
                'Boolean': None,
                'Float': None,
                'Datetime': '14/12/2030'
            },
            {
                'Id': 4,
                'Value': 'Value 4',
                'Optional': None,
                'Boolean': None,
                'Float': None,
                'Datetime': '2024-07-08 13:14:15'
            }

        ]

def mock_json_data_source() -> S3JsonDataSource:
    
    config1 = {
        'type': 'object1',
        'id_attribute': 'Id',
        'mappings': {
            'id': {
                'heading': 'Id',
                'type': 'int'
            },
            'value': {
                'heading': 'Value',
                'type': 'str'
            },
            'optional': {
                'heading': 'Optional',
                'type': 'str'
            },
            'boolean': {
                'heading': 'Boolean',
                'type': 'boolean'
            },
            'float': {
                'heading': 'Float',
                'type': 'float'
            },
            'datetime': {
                'heading': 'Datetime',
                'type': 'datetime'
            }
        }
    }
    
    s3ds = MockS3JsonDataSource(
        config=config1,
        secure=False,
        s3_endpoint='endpoint',
        s3_access_key='accesskey',
        s3_secret_key='secretkey',
        s3_bucket="test-bucket",
        s3_object="test.json"
    )
    core_data_object_mock = core_data_object(s3ds)
    return core_data_object_mock, s3ds

class TestS3JsonDataSource(TestCase):

    def test_attribute_types(self):
        _, jds = mock_json_data_source()
        expected = {
            'object1': {
                'id': 'int',
                'value': 'str',
                'optional': 'str',
                'boolean': 'boolean',
                'float': 'float',
                'datetime': 'datetime'
            }
        }
        self.assertEqual(expected, jds.attribute_types)
        self.assertEqual(['object1'], jds.supported_types)

    def test_get_by_id(self):
        _, jds = mock_json_data_source()

        ret = jds.get_by_id('object1', [1, 2, 4])
        obj1 = next(ret)
        self.assertEqual(1, obj1.id)
        self.assertEqual({
            'value': 'Value 1',
            'optional': 'YES',
            'boolean': True,
            'float': 2.34,
            'datetime': datetime(2024, 1, 1, 12, 13, 14)}, obj1.attributes)
        obj2 = next(ret)
        self.assertEqual(2, obj2.id)
        self.assertEqual({
            'value': 'Value 2',
            'optional': None,
            'boolean': False,
            'float': None,
            'datetime': None}, obj2.attributes)
        obj4 = next(ret)
        self.assertEqual(4, obj4.id)
        self.assertEqual({
            'value': 'Value 4',
            'optional': None,
            'boolean': None,
            'float': None,
            'datetime': datetime(2024, 7, 8, 13, 14, 15)}, obj4.attributes)
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list(self):
        _, jds = mock_json_data_source()

        ret = jds.get_list('object1')
        obj1 = next(ret)
        self.assertEqual(1, obj1.id)
        self.assertEqual({
            'value': 'Value 1',
            'optional': 'YES',
            'boolean': True,
            'float': 2.34,
            'datetime': datetime(2024, 1, 1, 12, 13, 14)}, obj1.attributes)
        obj2 = next(ret)
        self.assertEqual(2, obj2.id)
        self.assertEqual({
            'value': 'Value 2',
            'optional': None,
            'boolean': False,
            'float': None,
            'datetime': None}, obj2.attributes)
        obj3 = next(ret)
        self.assertEqual(3, obj3.id)
        self.assertEqual({
            'value': 'Value 3',
            'optional': 'NO',
            'boolean': None,
            'float': None,
            'datetime': datetime(2030, 12, 14)}, obj3.attributes)
        obj4 = next(ret)
        self.assertEqual(4, obj4.id)
        self.assertEqual({
            'value': 'Value 4',
            'optional': None,
            'boolean': None,
            'float': None,
            'datetime': datetime(2024, 7, 8, 13, 14, 15)}, obj4.attributes)
        with self.assertRaises(StopIteration):
            next(ret)
