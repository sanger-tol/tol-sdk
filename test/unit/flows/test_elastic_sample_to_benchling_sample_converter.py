# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

from tol.core import (
    DataObject,
    DataSource,
    core_data_object
)
from tol.core.operator import (
    Relational
)
from tol.core.relationship import (
    RelationshipConfig
)
from tol.flows.converters import (
    ElasticSampleToBenchlingSampleConverter
)


class _MockDataSource(DataSource, Relational):
    @property
    def supported_types(self):
        return ['sample', 'species', 'specimen', 'tolid']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'benchling_species': 'species',
            'benchling_specimen': 'specimen',
            'benchling_tolid': 'tolid'
        }
        return {'sample': rc_sample}

    def get_to_one_relation(
            self,
            source: DataObject,
            relationship_name: str
    ):
        to_one = getattr(source, 'to_one', {})
        return to_one.get(relationship_name) if to_one else None

    def get_to_many_relations(
            self
    ):
        raise NotImplementedError()


class TestElasticSampleToBenchlingSampleConverter(TestCase):
    def test_default_convert(self):

        source = _MockDataSource(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticSampleToBenchlingSampleConverter(
            data_object_factory=destination.data_object_factory
        )
        
        CoreDataObject = source.data_object_factory # noqa N806
        obj1 = CoreDataObject(
            id_='sample_id1',
            type_='sample',
            attributes={
                'benchling_another': 'another1'
            }
        )
        obj2 = CoreDataObject(
            id_='sample_id1',
            type_='sample',
            attributes={
                'benchling_eln_tissue_id': 'benchling1',
                'benchling_another': 'another1'
            },
            to_one={}
        )
        obj3 = [
            CoreDataObject(
                id_=f'sample_id{i}',
                type_='sample',
                attributes={
                    'benchling_eln_tissue_id': f'benchling{i}',
                    'benchling_another': f'another{i}'
                },
                to_one={}
            ) for i in range(3)
        ]

        # test for no benchling_eln_tissue_id
        converteds = list(converter.convert(obj1))
        self.assertEqual(len(converteds), 0)

        # test for missing relationships
        converteds = converter.convert(obj2)
        ret1 = next(converteds)
        self.assertEqual('benchling1', ret1.id)
        self.assertEqual('another1', ret1.attributes['another'])

        with self.assertRaises(StopIteration):
            next(converteds)
        
        # test for multiple objects
        converteds = []
        for obj in obj3:
            converteds.extend(list(converter.convert(obj)))
        self.assertEqual(len(converteds), 3)
        for i, converted in enumerate(converteds):
            self.assertEqual(f'benchling{i}', converted.id)
            self.assertEqual(f'another{i}', converted.attributes['another'])