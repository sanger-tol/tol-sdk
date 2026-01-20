# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import DataSource, core_data_object
from tol.flows.converters import PrefixFieldConverter


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


class TestPrefixFieldConverter(TestCase):

    def test_convert_adds_prefix_when_missing(self):
        source = _MockDataSource(config={})
        core_data_object(source)
        destination = _MockDataSourceDestination(config={})
        core_data_object(destination)
        mock_object = source.data_object_factory(
            'sample',
            'ABC123',
            attributes={
                'HAZARD_GROUP': '01',
                'SampleName': 'TestSample',
            }
        )
        config = PrefixFieldConverter.Config(
            field_name='HAZARD_GROUP',
            prefix='HG'
        )
        converter = PrefixFieldConverter(
            destination.data_object_factory,
            config
        )

        result = converter.convert(mock_object)
        converted_object = next(result)
        with self.assertRaises(StopIteration):
            next(result)

        self.assertEqual(converted_object.get_field_by_name('HAZARD_GROUP'), 'HG01')
        self.assertEqual(converted_object.get_field_by_name('SampleName'), 'TestSample')

    def test_convert_leaves_prefix_when_present(self):
        source = _MockDataSource(config={})
        core_data_object(source)
        destination = _MockDataSourceDestination(config={})
        core_data_object(destination)
        mock_object = source.data_object_factory(
            'sample',
            'ABC123',
            attributes={
                'HAZARD_GROUP': 'HG02',
                'SampleName': 'TestSample',
            }
        )
        config = PrefixFieldConverter.Config(
            field_name='HAZARD_GROUP',
            prefix='HG'
        )
        converter = PrefixFieldConverter(
            destination.data_object_factory,
            config
        )

        result = converter.convert(mock_object)
        converted_object = next(result)
        with self.assertRaises(StopIteration):
            next(result)

        self.assertEqual(converted_object.get_field_by_name('HAZARD_GROUP'), 'HG02')
        self.assertEqual(converted_object.get_field_by_name('SampleName'), 'TestSample')
