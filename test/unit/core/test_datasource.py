# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict
from unittest import TestCase

from tol.core import (
    DataSource,
    DataSourceError,
    unsupported,
    UnsupportedMethodException
)


class TestDataSourceExpected(DataSource):
    def __init__(self, config: Dict):
        super().__init__(config, expected=['field1', 'field2'])

    @unsupported
    def get_by_id(self, *args, **kwargs):
        pass

    @unsupported
    def get_list_page(self, *args, **kwargs):
        pass


class TestDataSourceNoExpected(DataSource):
    def __init__(self, config: Dict):
        super().__init__(config, expected=[])

    @unsupported
    def get_by_id(self, *args, **kwargs):
        pass

    def get_list_page(self, *args, **kwargs):
        return [{
            'hello': 'world'
        }]


class TestDataSource(TestCase):
    def test_expected_parameters(self):
        with self.assertRaises(DataSourceError):
            TestDataSourceExpected({})
        with self.assertRaises(DataSourceError):
            TestDataSourceExpected({'field1': 'value1'})
        TestDataSourceExpected({'field1': 'value1', 'field2': 'value2'})

    def test_no_expected_parameters(self):
        TestDataSourceNoExpected({})
        TestDataSourceNoExpected({'field1': 'value1'})
        TestDataSourceNoExpected({'field1': 'value1', 'field2': 'value2'})

    def test_unsupported_method_exception(self):
        with self.assertRaises(UnsupportedMethodException):
            TestDataSourceNoExpected({}).get_by_id()
