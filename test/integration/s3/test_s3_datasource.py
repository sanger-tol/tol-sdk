# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase
)

from tol.core import (
    core_data_object
)
from tol.s3 import (
    create_s3_datasource
)


class TestS3DataSource(TestCase):

    def test_attribute_types(self):
        s3ds = create_s3_datasource(bucket_name='tol-system-test-assets')
        core_data_object(s3ds)
        assert 'object' in s3ds.attribute_types

        assert s3ds.attribute_types['object']['bucket_name'] == 'str'
        assert s3ds.attribute_types['object']['last_modified'] == 'datetime'

    def test_get_list(self):
        s3ds = create_s3_datasource(bucket_name='tol-system-test-assets')
        core_data_object(s3ds)
        ret = list(s3ds.get_list('object'))
        obj_ids = [obj.id for obj in ret]
        assert 'test.json' in obj_ids
        assert 'prefix/file.json' in obj_ids
        assert len(obj_ids) == 2
        for obj in ret:
            if obj.id == 'test.json':
                self.assertEqual('test.json', obj.id)
                self.assertEqual(obj.bucket_name, 'tol-system-test-assets')
                self.assertIsNotNone(obj.last_modified)
            elif obj.id == 'prefix/file.json':
                self.assertEqual('prefix/file.json', obj.id)
                self.assertEqual(obj.bucket_name, 'tol-system-test-assets')
                self.assertIsNotNone(obj.last_modified)

    def test_get_list_no_prefix(self):
        s3ds = create_s3_datasource('tol-system-test-assets', 'prefix')
        core_data_object(s3ds)
        ret = list(s3ds.get_list('object'))
        obj_ids = [obj.id for obj in ret]
        assert 'prefix/file.json' in obj_ids
        assert len(obj_ids) == 1
        for obj in ret:
            if obj.id == 'prefix/file.json':
                self.assertEqual('prefix/file.json', obj.id)
                self.assertEqual(obj.bucket_name, 'tol-system-test-assets')
                self.assertIsNotNone(obj.last_modified)
