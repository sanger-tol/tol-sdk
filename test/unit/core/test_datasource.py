# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict
from unittest import TestCase

import pytest

from tol.core import DataSource, DataSourceError
from tol.core.datasource_error import NoDataObjectFactoryError
from tol.core.operator import PageGetter


class _TestDataSourceExpected(DataSource):
    def __init__(self, config: Dict):
        super().__init__(config, expected=['field1', 'field2'])

    @property
    def supported_types(self):
        raise NotImplementedError()

    @property
    def attribute_types(self):
        raise NotImplementedError()


ERROR_MESSAGE = "I don't like this."


class _TestDataSourceNoExpected(DataSource, PageGetter):
    def __init__(self, config: Dict):
        super().__init__(config, expected=[])

    def get_list_page(self, object_type: str, *args, **kwargs):
        return [{
            'hello': 'world'
        }]

    @property
    def supported_types(self):
        raise NotImplementedError()

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestDataSource(TestCase):
    def test_expected_parameters(self):
        with self.assertRaises(DataSourceError):
            _TestDataSourceExpected({})
        with self.assertRaises(DataSourceError):
            _TestDataSourceExpected({'field1': 'value1'})
        _TestDataSourceExpected({'field1': 'value1', 'field2': 'value2'})

    def test_no_expected_parameters(self):
        _TestDataSourceNoExpected({})
        _TestDataSourceNoExpected({'field1': 'value1'})
        _TestDataSourceNoExpected({'field1': 'value1', 'field2': 'value2'})

    def test_supported_method_no_exception(self):
        _TestDataSourceNoExpected({}).get_list_page('test')

    def test_no_object_factory(self):
        """
        Not setting the data_object_factory -> MisconfiguredDataSourceException
        """

        with pytest.raises(NoDataObjectFactoryError):
            _TestDataSourceNoExpected({}).data_object_factory
