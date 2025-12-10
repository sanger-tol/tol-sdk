# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import DataSource, core_data_object
from tol.flows.converters import SkipNullFieldsConverter


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


class TestRemoveNullFieldsConverter(TestCase):

    def test_convert_does_skip(self):
        source = _MockDataSource(config={})
        core_data_object(source)
        destination = _MockDataSourceDestination(config={})
        core_data_object(destination)
        mock_object = source.data_object_factory(
            'sample',
            'ABC123',
            attributes={
                'SpeciesID': None,
            }
        )
        config = SkipNullFieldsConverter.Config(
            field_names=['SpeciesID'],
        )
        converter = SkipNullFieldsConverter(
            destination.data_object_factory,
            config
        )

        result = converter.convert(mock_object)
        for res in result:
            assert res == None

        with self.assertRaises(StopIteration):
            next(result)
            
    def test_convert_does_not_skip(self):
        source = _MockDataSource(config={})
        core_data_object(source)
        destination = _MockDataSourceDestination(config={})
        core_data_object(destination)
        mock_object = source.data_object_factory(
            'sample',
            'ABC123',
            attributes={
                'SpeciesID': 'Value',
            }
        )
        config = SkipNullFieldsConverter.Config(
            field_names=['SpeciesID'],
        )
        converter = SkipNullFieldsConverter(
            destination.data_object_factory,
            config
        )

        result = converter.convert(mock_object)
        for res in result:
            assert res is not None
            assert res.attributes['SpeciesID'] == 'Value'

        with self.assertRaises(StopIteration):
            next(result)
