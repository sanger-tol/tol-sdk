# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    BioscanExtraPantheonSpeciesToElasticSampleUpdateConverter,
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['pantheon_species', 'sample']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestBioscanExtraPantheonSpeciesToElasticSampleUpdateConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BioscanExtraPantheonSpeciesToElasticSampleUpdateConverter(
            data_object_factory=destination.data_object_factory,
            config=BioscanExtraPantheonSpeciesToElasticSampleUpdateConverter.Config()
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='Genus species',
            type_='pantheon_species',
            attributes={
                'vernacular': '1',
                'conservation_status': '2',
                'larval_feeding_guild': '3',
                'adult_feeding_guild': '4',
                'broad_biotope': '5',
                'specific_assemblage_type': '6',
                'associations': '7',
                'link_to_assemblage': '8'
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(ret1, (None, {
            'bold_species': 'Genus species',
            'vernacular': '1',
            'conservation_status': '2',
            'larval_feeding_guild': '3',
            'adult_feeding_guild': '4',
            'broad_biotope': '5',
            'specific_assemblage_type': '6',
            'associations': '7',
            'link_to_assemblage': '8'
        }))
