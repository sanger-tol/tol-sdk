
# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import time
from unittest import TestCase

from tol.core import DataSource, core_data_object
from tol.flows.converters.time_string_to_time import TimeStringToTimeConverter


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestTimeStringToTimeConverter(TestCase):

    def setUp(self):
        self.source = _MockDataSource(config={})
        core_data_object(self.source)

    def test_hhmm_string(self):
        mock_object = self.source.data_object_factory(
            'sample',
            'ABC123',
            attributes={
                'TIME_OF_COLLECTION': '13:58',
                'SampleName': 'TestSample',
            }
        )
        config = TimeStringToTimeConverter.Config(field_names=['TIME_OF_COLLECTION'])
        converter = TimeStringToTimeConverter(
            self.source.data_object_factory,
            config
        )

        result = converter.convert(mock_object)
        converted_object = next(result)
        with self.assertRaises(StopIteration):
            next(result)

        self.assertIsInstance(converted_object.get_field_by_name('TIME_OF_COLLECTION'), time)
        self.assertEqual(converted_object.get_field_by_name('TIME_OF_COLLECTION'), time(13, 58))
        self.assertEqual(converted_object.get_field_by_name('SampleName'), 'TestSample')

    def test_hhmmss_string(self):
        mock_object = self.source.data_object_factory(
            'sample',
            'ABC123',
            attributes={
                'TIME_OF_COLLECTION': '13:58:12',
                'SampleName': 'TestSample',
            }
        )
        config = TimeStringToTimeConverter.Config(field_names=['TIME_OF_COLLECTION'])
        converter = TimeStringToTimeConverter(
            self.source.data_object_factory,
            config
        )

        result = converter.convert(mock_object)
        converted_object = next(result)
        with self.assertRaises(StopIteration):
            next(result)

        self.assertIsInstance(converted_object.get_field_by_name('TIME_OF_COLLECTION'), time)
        self.assertEqual(
            converted_object.get_field_by_name('TIME_OF_COLLECTION'), time(13, 58, 12)
        )

    def test_invalid_string(self):
        mock_object = self.source.data_object_factory(
            'sample',
            'ABC123',
            attributes={
                'TIME_OF_COLLECTION': 'not_a_time',
                'SampleName': 'TestSample',
            }
        )
        config = TimeStringToTimeConverter.Config(field_names=['TIME_OF_COLLECTION'])
        converter = TimeStringToTimeConverter(
            self.source.data_object_factory,
            config
        )

        result = converter.convert(mock_object)
        converted_object = next(result)
        with self.assertRaises(StopIteration):
            next(result)

        # Should remain unchanged
        self.assertEqual(converted_object.get_field_by_name('TIME_OF_COLLECTION'), 'not_a_time')

    def test_already_time(self):
        mock_object = self.source.data_object_factory(
            'sample',
            'ABC123',
            attributes={
                'TIME_OF_COLLECTION': time(9, 30),
                'SampleName': 'TestSample',
            }
        )
        config = TimeStringToTimeConverter.Config(field_names=['TIME_OF_COLLECTION'])
        converter = TimeStringToTimeConverter(
            self.source.data_object_factory,
            config
        )

        result = converter.convert(mock_object)
        converted_object = next(result)
        with self.assertRaises(StopIteration):
            next(result)

        self.assertEqual(converted_object.get_field_by_name('TIME_OF_COLLECTION'), time(9, 30))
