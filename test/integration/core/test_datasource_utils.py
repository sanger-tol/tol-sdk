# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase
)

from tol.core import (
    DataSourceUtils
)
from tol.sources import (
    portaldb
)


class TestDataSourceUtils(TestCase):

    def __get_ds():
        dsi = portaldb().get_one('data_source_instance', '18')
        return DataSourceUtils.get_datasource_by_datasource_instance(dsi)

    def test_attribute_types(self):
        ds = self.__get_ds()

        assert 'record' in ds.attribute_types
        assert ds.attribute_types['record']['name'] == 'str'
        assert ds.attribute_metadata['record']['big_string']['display_name'] == 'Big String'
        assert ds.attribute_metadata['record']['big_string']['description'] is not None

    def test_relationship_config(self):
        ds = self.__get_ds()

        assert 'record' in ds.relationship_config
        assert ds.relationship_config['record'].to_many['children'] == 'child'
        assert 'child' in ds.relationship_config
        assert ds.relationship_config['child'].to_one['record'] == 'record'

    def test_get_by_id(self):
        ds = self.__get_ds()

        obj1 = ds.get_one('record', 'test-1')
        self.assertEqual('test-1', obj1.id)

        # Just pick out a few attributes here to test
        self.assertEqual(obj1.little_string, 'b')
        self.assertEqual(obj1.bool, False)
        self.assertEqual(obj1.int, 1)
        self.assertEqual(obj1.calc_double_the_int, 2)  # Calculated attribute
