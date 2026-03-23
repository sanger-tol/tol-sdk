# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import DataSource, core_data_object
from tol.flows.converters import DefaultFieldValueIfMissingConverter


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestDefaultFieldValueIfMissingConverter(TestCase):

    def test_convert(self):
        source = _MockDataSource(config={})
        core_data_object(source)
        mock_object = source.data_object_factory(
            'sample',
            'sample1',
            attributes={
                'FIELD1': 'VALUE1',
                # 'FIELD2' is missing
                'FIELD3': '',
                'FIELD4': None
            }
        )

        config = DefaultFieldValueIfMissingConverter.Config(
            field_name='FIELD2',
            default_value='DEFAULT2'
        )
        converter = DefaultFieldValueIfMissingConverter(
            source.data_object_factory, config
        )

        result = converter.convert(mock_object)

        ret = next(result)
        assert ret.attributes['FIELD1'] == 'VALUE1'
        assert ret.attributes['FIELD2'] == 'DEFAULT2'
        assert ret.attributes['FIELD3'] == ''
        assert ret.attributes['FIELD4'] is None

        with self.assertRaises(StopIteration):
            next(result)
