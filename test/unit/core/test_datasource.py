# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict
from unittest import TestCase

import pytest

from tol.core import (
    DataSourceError,
    ReadOnlyDataSource,
    UnsupportedOperationException,
    unsupported
)


class TestDataSourceExpected(ReadOnlyDataSource):
    def __init__(self, config: Dict):
        super().__init__(config, expected=['field1', 'field2'])

    @unsupported()
    def get_by_id(self, object_type: str, *args, **kwargs):
        pass

    @unsupported()
    def get_list_page(self, object_type: str, *args, **kwargs):
        pass

    @unsupported()
    def get_list(self, object_type: str, *args, **kwargs) -> None:
        pass


ERROR_MESSAGE = "I don't like this."


class TestDataSourceNoExpected(ReadOnlyDataSource):
    def __init__(self, config: Dict):
        super().__init__(config, expected=[])

    @unsupported(message=ERROR_MESSAGE)
    def get_by_id(self, object_type: str, *args, **kwargs):
        pass

    def get_list_page(self, object_type: str, *args, **kwargs):
        return [{
            'hello': 'world'
        }]

    # decorate without parentheses
    @unsupported
    def get_list(self, object_type: str, *args, **kwargs) -> None:
        pass


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
        ds_1 = TestDataSourceExpected({'field1': 'value1', 'field2': 'value2'})
        with pytest.raises(UnsupportedOperationException):
            ds_1.get_list_page('test')

        ds_2 = TestDataSourceNoExpected({})
        with pytest.raises(
            UnsupportedOperationException,
            match=rf'.*{ERROR_MESSAGE}'
        ):
            ds_2.get_by_id('test')

    def test_unsupported_method_doc(self):
        method = TestDataSourceNoExpected({}).get_by_id
        self.assertTrue(hasattr(method, '_unsupported'))
        self.assertTrue(method._unsupported)

    def test_supported_method_no_exception(self):
        TestDataSourceNoExpected({}).get_list_page('test')

    def test_supported_method_no_doc(self):
        self.assertFalse(
            hasattr(
                TestDataSourceNoExpected({}).get_list_page,
                '_unsupported'
            )
        )

    def test_get_supported_methods(self):
        # first has no supported methods
        self.assertEqual(
            TestDataSourceExpected(
                {'field1': 'value1', 'field2': 'value2'}
            ).supported_operations,
            []
        )
        # second supports one
        self.assertEqual(
            TestDataSourceNoExpected({}).supported_operations,
            ['get_list_page']
        )
