# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    ElasticSpeciesToStsSpeciesConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['species']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestElasticSpeciesToStsSpeciesConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticSpeciesToStsSpeciesConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806

        obj1 = CoreDataObject(
            id_='test1',
            type_='species',
            attributes={
                'sts_species_id': 123,
                'goat_genome_size': 123456789.9,
                'goat_family_representative': ['PROJ1'],
                'goat_echabs92': ['echabs1'],
                'goat_habreg_2017': ['habreg1', 'habreg2'],
                'goat_marhabreg-2017': ['marhabreg1', 'marhabreg2'],
                'goat_waca_1981': ['waca1'],
                'goat_isb_wildlife_act_1976': ['isb1'],
                'goat_protection_of_badgers_act_1992': ['badger1'],
                'tolid_prefix': 'abCdeFghi'
            }
        )
        obj2 = CoreDataObject(
            id_='test2',
            type_='species',
            attributes={
                'sts_species_id': 456
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(123, ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'genome_size': 123456789.9,
            'family_representative': ['PROJ1'],
            'legislation': json.dumps({
                'echabs92': ['echabs1'],
                'habreg_2017': ['habreg1', 'habreg2'],
                'marhabreg-2017': ['marhabreg1', 'marhabreg2'],
                'waca_1981': ['waca1'],
                'isb_wildlife_act_1976': ['isb1'],
                'protection_of_badgers_act_1992': ['badger1']
            }, default=str),
            'prefix': 'abCdeFghi'
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(456, ret2.id)
        self.assertEqual(obj2.type, ret2.type)
        self.assertEqual(ret2.attributes, {
            'genome_size': None,
            'family_representative': None,
            'legislation': None,
            'prefix': None
        })

        with self.assertRaises(StopIteration):
            next(converteds)
