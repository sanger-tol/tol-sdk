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
    StsSpeciesToElasticSpeciesConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['sequencing_material_status', 'species', 'species_lab_work_status']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_species = RelationshipConfig()
        rc_species.to_one = {
            'sequencing_material_status': 'sequencing_material_status'
        }
        rc_species.to_many = {
            'species_lab_work_statuses': 'species_lab_work_status'
        }
        return {'species': rc_species}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        if source.id == 'test1':
            return source._host.data_object_factory(
                id_='test1',
                type_='sequencing_material_status',
                attributes={'status': 'status1'}
            )

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str
    ):
        if source.id == 'test1':
            return [
                source._host.data_object_factory(
                    id_='test1',
                    type_='species_lab_work_status',
                    attributes={'status': 'value1'}
                ),
                source._host.data_object_factory(
                    id_='test2',
                    type_='species_lab_work_status',
                    attributes={'status': 'value2'}
                )
            ]
        return []


class _MockDataSource(DataSource):

    @property
    def supported_types(self):
        return ['species']

    @property
    def attribute_types(self):
        raise NotImplementedError()


class TestStsSpeciesToElasticSpeciesConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = StsSpeciesToElasticSpeciesConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        sequencing_material_status = CoreDataObject(
            id_='test1',
            type_='sequencing_material_status',
            attributes={'status': 'status1'}
        )
        obj1 = CoreDataObject(
            id_='test1',
            type_='species',
            attributes={'attribute1': 'value1'},
            to_one={'sequencing_material_status': sequencing_material_status}
        )
        obj2 = CoreDataObject(
            id_='test2',
            type_='species',
            attributes={'attribute1': 'value2'}
        )
        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'attribute1': 'value1',
            'sequencing_material_status': 'status1',
            'lab_work_status': ['value1', 'value2']
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.id, ret2.id)
        self.assertEqual(obj2.type, ret2.type)
        self.assertEqual(ret2.attributes, {
            'attribute1': 'value2'
        })

        with self.assertRaises(StopIteration):
            next(converteds)
