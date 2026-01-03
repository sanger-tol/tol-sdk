# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import DataSource, core_data_object
from tol.flows.converters import CombineFieldsToFieldConverter


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceDestination(DataSource):
    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestCombineFieldsToFieldConverter(TestCase):

    def test_convert_does_not_add_public_name_if_missing_field(self):
        source = _MockDataSource(config={})
        core_data_object(source)
        destination = _MockDataSourceDestination(config={})
        core_data_object(destination)

        mock_object = source.data_object_factory(
            'sample',
            'ABC124',
            attributes={
                'TOLID_PREFIX': 'TOL',
            }
        )

        config = CombineFieldsToFieldConverter.Config(
            field1='TOLID_PREFIX',
            field2='SPECIMEN_ID',
            dest_field='public_name',
            lowercase_field1=True,
        )
        converter = CombineFieldsToFieldConverter(
            destination.data_object_factory,
            config
        )

        result = list(converter.convert(mock_object))
        converted_object = result[0]

        self.assertIsNone(
            converted_object.get_field_by_name('public_name')
        )

    def test_convert_adds_public_name_lowercase(self):
        source = _MockDataSource(config={})
        core_data_object(source)
        destination = _MockDataSourceDestination(config={})
        core_data_object(destination)
        mock_object = source.data_object_factory(
            'sample',
            'ABC123',
            attributes={
                'TOLID_PREFIX': 'TOL',
                'SPECIMEN_ID': '001',
            }
        )
        config = CombineFieldsToFieldConverter.Config(
            field1='TOLID_PREFIX',
            field2='SPECIMEN_ID',
            dest_field='public_name',
            lowercase_field1=True,
        )
        converter = CombineFieldsToFieldConverter(
            destination.data_object_factory,
            config
        )

        result = converter.convert(mock_object)
        result_list = list(result)
        assert len(result_list) == 1
        converted_object = result_list[0]
        assert converted_object.get_field_by_name('public_name') == 'tol001'

    def test_convert_adds_public_name_no_lowercase(self):
        source = _MockDataSource(config={})
        core_data_object(source)
        destination = _MockDataSourceDestination(config={})
        core_data_object(destination)
        mock_object = source.data_object_factory(
            'sample',
            'ABC123',
            attributes={
                'TOLID_PREFIX': 'TOL',
                'SPECIMEN_ID': '002',
            }
        )
        config = CombineFieldsToFieldConverter.Config(
            field1='TOLID_PREFIX',
            field2='SPECIMEN_ID',
            dest_field='public_name',
            lowercase_field1=False,
        )
        converter = CombineFieldsToFieldConverter(
            destination.data_object_factory,
            config
        )

        result = converter.convert(mock_object)
        result_list = list(result)
        assert len(result_list) == 1
        converted_object = result_list[0]
        assert converted_object.get_field_by_name('public_name') == 'TOL002'
