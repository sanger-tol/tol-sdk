# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    TolqcSpeciesToElasticSpeciesConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['species']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestTolqcSpeciesToElasticSpeciesConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = TolqcSpeciesToElasticSpeciesConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='Abax parallelepipedus',
            type_='species',
            attributes={'chromosome_number': '35',
                        'taxon_family': 'Carabidae',
                        'taxon_group': 'insects',
                        'taxon_id': '102642',
                        'taxon_order': 'Coleoptera',
                        'taxon_phylum': 'Arthropoda'
                        }
        )
        obj2 = CoreDataObject(
            id_='Abdera quadrifasciata',
            type_='species',
            attributes={'chromosome_number': '20',
                        'taxon_family': 'Melandryidae',
                        'taxon_group': 'insects',
                        'taxon_id': '433183',
                        'taxon_order': 'Coleoptera',
                        'taxon_phylum': 'Arthropoda'
                        }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.attributes['taxon_id'], ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'chromosome_number': '35',
            'family': 'Carabidae',
            'group': 'insects',
            'order_group': 'Coleoptera',
            'taxon_group': 'Arthropoda',
            'scientific_name': 'Abax parallelepipedus'
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.attributes['taxon_id'], ret2.id)
        self.assertEqual(obj2.type, ret2.type)
        self.assertEqual(ret2.attributes, {
            'chromosome_number': '20',
            'family': 'Melandryidae',
            'group': 'insects',
            'order_group': 'Coleoptera',
            'taxon_group': 'Arthropoda',
            'scientific_name': 'Abdera quadrifasciata'
        })

        with self.assertRaises(StopIteration):
            next(converteds)
