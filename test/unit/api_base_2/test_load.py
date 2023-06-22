# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base2.load import LoadedDataObject, UpsertLoader
from tol.core import core_data_object


CoreDataObject = core_data_object()  # noqa


class TestLoadedDataObject:
    def test_no_relationships(self):
        """A simple object, with attributes but no relationships"""
        attributes = {
            'lol': True,
            'int': 23890,
            'float': 0.23
        }
        object_dump = {
            'type': 'test',
            '_uuid': 'abc',
            'id': '3948',
            'attributes': attributes
        }
        loaded_object = LoadedDataObject(object_dump)

        assert loaded_object.id == '3948'
        assert loaded_object.type == 'test'
        assert loaded_object.attributes == attributes
        assert loaded_object.to_one_relationships == {}
        assert loaded_object.to_many_relationships == {}

    def test_to_one_relationship(self):
        """A to-one reference"""
        object_dump = {
            'type': 'test',
            '_uuid': 'abc',
            'relationships': {
                'one': {
                    'hype': 'train'
                }
            }
        }
        hype_object = CoreDataObject('hype', id_='indeed')
        uuid_object_dict = {
            'train': hype_object
        }

        loaded_object = LoadedDataObject(object_dump)
        loaded_object.configure_relationships(uuid_object_dict)

        assert loaded_object.type == 'test'
        assert loaded_object.id is None
        assert loaded_object.attributes == {}
        assert loaded_object.to_one_relationships == {
            'hype': hype_object
        }
        assert loaded_object.to_many_relationships == {}

    def test_several_many_relationships(self):
        """Several to-many relationships on same object"""
        many_relations = [
            CoreDataObject(f'many_{i}')
            for i in range(32)
        ]
        many_uuids = [
            f'uuid-{r.type}' for r in many_relations
        ]
        uuid_object_dict = dict(zip(many_uuids, many_relations))
        object_dump = {
            'type': 'nice',
            '_uuid': 'abc',
            'relationships': {
                'many': {
                    str(i): [uuid]
                    for i, uuid in enumerate(many_uuids)
                }
            }
        }

        loaded_object = LoadedDataObject(object_dump)
        loaded_object.configure_relationships(uuid_object_dict)

        assert loaded_object.type == 'nice'
        assert loaded_object.id is None
        assert loaded_object.attributes == {}
        assert loaded_object.to_one_relationships == {}
        assert loaded_object.to_many_relationships == {
            str(i): [relation]
            for i, relation in enumerate(many_relations)
        }

    def test_complex(self):
        """Many attributes + both kinds of relationships"""
        attributes = {
            'lol': True,
            'int': 23890,
            'float': 0.23
        }
        hype_object = CoreDataObject('hype', id_='indeed')
        many_relations = [
            CoreDataObject(f'many_{i}')
            for i in range(32)
        ]
        many_uuids = [
            f'uuid-{r.type}' for r in many_relations
        ]
        uuid_dict_manys = dict(zip(many_uuids, many_relations))
        uuid_object_dict = {
            'train': hype_object,
            **uuid_dict_manys
        }
        object_dump = {
            'type': 'test',
            '_uuid': 'abc',
            'id': '3948',
            'attributes': attributes,
            'relationships': {
                'one': {
                    'hype': 'train'
                },
                'many': {
                    str(i): [uuid]
                    for i, uuid in enumerate(many_uuids)
                }
            }
        }

        loaded_object = LoadedDataObject(object_dump)
        loaded_object.configure_relationships(uuid_object_dict)

        assert loaded_object.type == 'test'
        assert loaded_object.id == '3948'
        assert loaded_object.attributes == attributes
        assert loaded_object.to_one_relationships == {
            'hype': hype_object
        }
        assert loaded_object.to_many_relationships == {
            str(i): [relation]
            for i, relation in enumerate(many_relations)
        }


class TestUpsertLoader:
    def test_single_object(self):
        """A single object with no relationships"""
        attributes = {
            'lol': True,
            'int': 23890,
            'float': 0.23
        }
        object_dump = {
            'type': 'test',
            '_uuid': 'abc',
            'id': '3948',
            'attributes': attributes
        }
        upsert_dump = {
            'data': [object_dump]
        }

        loaded_objects = UpsertLoader().load(upsert_dump)

        # only 1 object
        assert len(loaded_objects) == 1
        # fields are correct
        loaded_object = loaded_objects[0]
        assert loaded_object.type == 'test'
        assert loaded_object.id == '3948'
        assert loaded_object.attributes == attributes
        assert loaded_object.to_one_relationships == {}
        assert loaded_object.to_many_relationships == {}

    def test_to_one_reference_chain(self):
        """A chain of objects linked by to-one references"""
        one_chain = [
            {
                'type': f'chain_{"Z" * i}',
                '_uuid': str(i),
                'relationships': {
                    'one': {
                        'next': str(i + 1)
                    }
                }
            }
            for i in range(29)
        ]
        upsert_dump = {
            'data': [
                *one_chain,
                {
                    'type': 'end',
                    '_uuid': '29'
                }
            ]
        }

        loaded_objects = UpsertLoader().load(upsert_dump)

        # correct number of objects
        assert len(loaded_objects) == 30
        sorted_objects = sorted(
            loaded_objects,
            key=lambda d: d.type
        )

        for i, first in enumerate(sorted_objects):
            if i >= 29:
                break
            second = loaded_objects[i + 1]
            # assert fields are correct
            assert first.to_one_relationships == {
                'next': second
            }

    def test_several_to_many_relationships(self):
        """Several to-many relationships on the same object"""
        many_objects_dump = [
            {
                'type': f'many_{"A" * i}',
                '_uuid': str(i),
            }
            for i in range(51)
        ]
        upsert_dump = {
            'data': [
                *many_objects_dump,
                {
                    'type': 'source',
                    '_uuid': 'testLol',
                    'relationships': {
                        'many': {
                            f'many_{"A" * i}': [str(i)]
                            for i in range(51)
                        }
                    }
                }
            ]
        }

        loaded_objects = UpsertLoader().load(upsert_dump)

        # correct number of objects
        assert len(loaded_objects) == 52

        # populated correctly
        objects_dict = {d.type: d for d in loaded_objects}
        # all unique
        assert len(objects_dict) == 52
        source_object = objects_dict.pop('source')
        many_dict = {
            k: [data_object]
            for k, data_object in objects_dict.items()
        }
        # relationships for many are correct
        assert source_object.to_many_relationships == many_dict
