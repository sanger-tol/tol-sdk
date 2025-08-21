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
    TreeofsexSpeciesToTreeofsexwhSpeciesConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['attribute', 'attribute_key', 'species']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_species = RelationshipConfig()
        rc_species.to_many = {
            'atts': 'attribute'
        }
        rc_attribute = RelationshipConfig()
        rc_attribute.to_one = {
            'attribute_key': 'attribute_key'
        }
        return {'species': rc_species, 'attribute': rc_attribute}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        if source.id == 'test1':
            return source._host.data_object_factory(
                id_='test1',
                type_='sequencing_material_status',
                attributes={
                    'status': 'status1'
                }
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
                    type_='attribute',
                    attributes={
                        'value': 'att1'
                    },
                    to_one={
                        'attribute_key': source._host.data_object_factory(
                            id_='key1',
                            type_='attribute_key',
                            attributes={}
                        )
                    }
                ),
                source._host.data_object_factory(
                    id_='test2',
                    type_='attribute',
                    attributes={
                        'value': 'att2'
                    },
                    to_one={
                        'attribute_key': source._host.data_object_factory(
                            id_='key2',
                            type_='attribute_key',
                            attributes={}
                        )
                    }
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


class TestTreeofsexSpeciesToTreeofsexwhSpeciesConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = TreeofsexSpeciesToTreeofsexwhSpeciesConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory  # noqa N806
        obj1 = CoreDataObject(
            id_='test1',
            type_='species',
            attributes={},
        )
        obj2 = CoreDataObject(
            id_='test2',
            type_='species',
            attributes={}
        )
        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual(obj1.type, ret1.type)
        self.assertEqual(ret1.attributes, {
            'key1': 'att1',
            'key2': 'att2',
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(obj2.id, ret2.id)
        self.assertEqual(obj2.type, ret2.type)
        self.assertEqual(ret2.attributes, {})

        with self.assertRaises(StopIteration):
            next(converteds)
