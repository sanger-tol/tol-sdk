# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import DataSource, core_data_object
from tol.flows.converters import IncomingSampleToIncomingSampleWithListsConverter


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['upload']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestIncomingSampleToIncomingSampleWithListsConverter(TestCase):
    def test_convert(self):
        source = _MockDataSource(config={})
        core_data_object(source)
        mock_object = source.data_object_factory(
            'upload',
            'sample1',
            attributes={
                'ORGANISM_PART': 'PART1 | PART2 | PART3',
                'LIFESTAGE': 'STAGE1 | STAGE2'
            }
        )

        config = IncomingSampleToIncomingSampleWithListsConverter.Config(
            fields_to_convert=['ORGANISM_PART', 'LIFESTAGE'],
            separator='|'
        )
        converter = IncomingSampleToIncomingSampleWithListsConverter(
            source.data_object_factory, config
        )

        result = converter.convert(mock_object)

        ret = next(result)
        assert ret.attributes['ORGANISM_PART'] == ['PART1', 'PART2', 'PART3']
        assert ret.attributes['LIFESTAGE'] == ['STAGE1', 'STAGE2']

        with self.assertRaises(StopIteration):
            next(result)
