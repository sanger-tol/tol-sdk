# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

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


def json_data_source() -> S3JsonDataSource:
    jds = S3JsonDataSource({
        'uri': 's3://tol-system-test-assets/test.json',
        'type': 'object1',
        'id_attribute': 'Id',
        's3_host': 'cog.sanger.ac.uk',
        's3_access_key': os.getenv('MINIO_ACCESS_KEY'),
        's3_secret_key': os.getenv('MINIO_SECRET_KEY'),
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
    })
    cdo = core_data_object(jds)
    return cdo, jds


class TestS3JsonDataSource(TestCase):

    def test_attribute_types(self):
        _, jds = json_data_source()
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
        _, gsds = json_data_source()

        ret = gsds.get_by_id('object1', [1, 4])
        obj1 = next(ret)
        self.assertEqual(1, obj1.id)
        self.assertEqual({
            'value': 'Value 1',
            'optional': 'YES',
            'boolean': True,
            'float': 2.34,
            'datetime': datetime(2024, 3, 15, 12, 13, 14)}, obj1.attributes)
        obj4 = next(ret)
        self.assertEqual(4, obj4.id)
        self.assertEqual({
            'value': 'Value 4',
            'optional': None,
            'boolean': None,
            'float': 5.678,
            'datetime': None}, obj4.attributes)
        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_list(self):
        _, gsds = json_data_source()

        ret = gsds.get_list('object1')
        obj1 = next(ret)
        self.assertEqual(1, obj1.id)
        self.assertEqual({
            'value': 'Value 1',
            'optional': 'YES',
            'boolean': True,
            'float': 2.34,
            'datetime': datetime(2024, 3, 15, 12, 13, 14)}, obj1.attributes)
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
            'boolean': True,
            'float': None,
            'datetime': datetime(2030, 12, 31)}, obj3.attributes)
        obj4 = next(ret)
        self.assertEqual(4, obj4.id)
        self.assertEqual({
            'value': 'Value 4',
            'optional': None,
            'boolean': None,
            'float': 5.678,
            'datetime': None}, obj4.attributes)
        with self.assertRaises(StopIteration):
            next(ret)
