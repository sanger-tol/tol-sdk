# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataSource,
    core_data_object
)
from tol.core.operator import (
    Relational
)
from tol.core.relationship import RelationshipConfig
from tol.flows.converters import (
    GoatTaxonToElasticSpeciesConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['taxon']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_taxon = RelationshipConfig()
        rc_taxon.to_one = {
            'genus': 'taxon',
            'family': 'taxon',
            'order': 'taxon'
        }
        return {'taxon': rc_taxon}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        if source.id == 'test1':
            return source._host.data_object_factory(
                id_='test1',
                type_='taxon',
                attributes={'scientific_name': 'Test'}
            )

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()

    def get_ranks(self):
        return ['genus', 'family', 'order']


class _MockDataSource(DataSource):

    @property
    def supported_types(self):
        return ['species']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestGoatTaxonToElasticSpeciesConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = GoatTaxonToElasticSpeciesConverter(
            data_object_factory=destination.data_object_factory,
            config=GoatTaxonToElasticSpeciesConverter.Config()
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        genus = CoreDataObject(
            id_='genus1',
            type_='taxon',
            attributes={'scientific_name': 'Test'}
        )
        obj1 = CoreDataObject(
            id_='1',
            type_='taxon',
            attributes={'taxon_rank': 'species'},
            to_one={'genus': genus}
        )
        obj2 = CoreDataObject(
            id_='2',
            type_='taxon',
            attributes={'scientific_name': 'Test test'}
        )
        obj3 = CoreDataObject(
            id_='species3',
            type_='taxon',
            attributes={'scientific_name': 'Not an integer ID'}
        )
        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual('species', ret1.type)
        self.assertEqual(ret1.attributes, {
            'taxon_rank': 'species',
            'genus_name': 'Test'
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.id, ret2.id)
        self.assertEqual('species', ret2.type)
        self.assertEqual(ret2.attributes, {
            'scientific_name': 'Test test'
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        # This has got a non-integer ID so we will not convert it
        converteds = converter.convert(obj3)

        with self.assertRaises(StopIteration):
            next(converteds)
