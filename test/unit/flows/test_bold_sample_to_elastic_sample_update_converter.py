# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    BoldSampleToElasticSampleUpdateConverter
)


class _MockDataSourceBold(DataSource):

    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockDataSourceElastic(DataSource):
    @property
    def supported_types(self):
        return ['sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestBoldSampleToElasticSampleUpdateConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceBold(config={})
        destination = _MockDataSourceElastic(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BoldSampleToElasticSampleUpdateConverter(
            data_object_factory=destination.data_object_factory,
            config=BoldSampleToElasticSampleUpdateConverter.Config()
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='BOLD1',
            type_='sample',
            attributes={
                'species': 'Species name',
                'taxid': 1234,
                'other': 'other'
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(ret1, (None, {
            'specimen.id': 'BOLD1',
            'species': 'Species name',
            'taxid': 1234,
            'other': 'other',
        }))

        obj2 = CoreDataObject(
            id_='BOLD2',
            type_='sample',
            attributes={
                'species': None,
                'taxid': 1234,
                'other': 'other'
            }
        )

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(ret2, (None, {
            'specimen.id': 'BOLD2',
            'species': None,
            'taxid': 1234,
            'other': 'other',
        }))
