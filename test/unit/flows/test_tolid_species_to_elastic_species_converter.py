# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataSource,
    core_data_object
)
from tol.flows.converters import (
    TolidSpeciesToElasticSpeciesConverter
)


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['species']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class _MockElasticDataSource(DataSource):
    @property
    def supported_types(self):
        return ['species']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestTolidSpeciesToElasticSpeciesConverter(TestCase):
    def test_convert(self):

        source = _MockDataSource(config={})
        destination = _MockElasticDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = TolidSpeciesToElasticSpeciesConverter(
            data_object_factory=destination.data_object_factory,
            config=TolidSpeciesToElasticSpeciesConverter.Config()
        )

        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='9606',
            type_='species',
            attributes={
                'name': 'Abdera quadrifasciata',
                'prefix': 'abCdeFghi',
                'genus': 'Abdera',
                'common_name': 'None'
            }
        )

        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'scientific_name': 'Abdera quadrifasciata',
            'tolid_prefix': 'abCdeFghi',
            'genus': 'Abdera'
        })

        with self.assertRaises(StopIteration):
            next(converteds)
