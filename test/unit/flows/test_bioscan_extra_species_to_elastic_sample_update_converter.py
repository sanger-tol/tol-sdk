# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    BioscanExtraSpeciesToElasticSampleUpdateConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['sample', 'species']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestBioScanExtraSpeciesToElasticSpeciesUpdateConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = BioscanExtraSpeciesToElasticSampleUpdateConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='Genus species',
            type_='species',
            attributes={
                'conservation_status': 'Bad',
            }
        )

        obj2 = CoreDataObject(
            id_='Genus2 species2',
            type_='species',
            attributes={
                'conservation_status': 'Good',
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(ret1, (None, {
            'bold_species': 'Genus species',
            'conservation_status': 'Bad'
        }))

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(ret2, (None, {
            'bold_species': 'Genus2 species2',
            'conservation_status': 'Good'
        }))
