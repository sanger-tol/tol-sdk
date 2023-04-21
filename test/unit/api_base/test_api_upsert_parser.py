# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, List
from uuid import uuid4

from tol.api_base.datasource import ApiUpsertParser
from tol.core import DataObject


class TestApiUpsertParser:
    def test_single_object(self):
        """
        Single object dump, no relationships
        """
        parser = ApiUpsertParser()
        obj = {
            'type': 'test',
            'id': '1234',
            '_uuid': uuid4().hex,
            'attributes': {
                'hype': 'train',
                'lol': 'indeed!'
            }
        }
        expected = [
            {
                'type': 'test',
                'id': '1234',
                'attributes': {
                    'hype': 'train',
                    'lol': 'indeed!'
                },
                'one': {},
                'many': {}
            }
        ]
        observed = self.__dump_data_objects_list(
            parser.parse([obj])
        )
        assert observed == expected

    def test_several_unrelated_objects(self):
        """
        Tests many objects with no relationship between them
        """
        parser = ApiUpsertParser()
        obj1 = {
            'type': 'test',
            'id': '1234',
            '_uuid': uuid4().hex,
            'attributes': {
                'hype': 'train',
                'lol': 'indeed!'
            }
        }
        obj2 = {
            'type': 'test',
            'id': '5678',
            '_uuid': uuid4().hex,
            'attributes': {
                'hype': 'df',
                'lol': 'free -h'
            }
        }
        expected = [
            {
                'type': 'test',
                'id': '1234',
                'attributes': {
                    'hype': 'train',
                    'lol': 'indeed!'
                },
                'one': {},
                'many': {}
            },
            {
                'type': 'test',
                'id': '5678',
                'attributes': {
                    'hype': 'df',
                    'lol': 'free -h'
                },
                'one': {},
                'many': {}
            }
        ]
        observed = self.__dump_data_objects_list(
            parser.parse([obj1, obj2])
        )
        assert observed == expected

    def test_to_one_relationship_pair(self):
        """
        Tests two objects, with one pointing to the other by a
        to-one relationship
        """
        __uuid = uuid4().hex
        obj1 = {
            'type': 'test',
            'id': 'hello',
            '_uuid': __uuid
        }
        obj2 = {
            'type': 'testlol',
            'id': 'adsflkhjld',
            '_uuid': uuid4().hex,
            'relationships': {
                'one': {
                    'testhype': __uuid
                }
            }
        }
        parsed = ApiUpsertParser().parse([obj2, obj1])
        # get obj1 out
        parsed_obj1s = [o for o in parsed if o.type == 'test']
        assert len(parsed_obj1s) == 1
        parsed_obj1 = parsed_obj1s[0]
        # construct the expected
        expected = [
            {
                'type': 'test',
                'id': 'hello',
                'attributes': {},
                'one': {},
                'many': {}
            },
            {
                'type': 'testlol',
                'id': 'adsflkhjld',
                'attributes': {},
                'one': {
                    'testhype': parsed_obj1
                },
                'many': {}
            }
        ]
        observed = self.__dump_data_objects_list(
            sorted(parsed, key=lambda p: (p.type, p.id))
        )
        assert expected == observed

    def test_to_many_relationship(self):
        """
        Tests N+1 objects, with N pointing to 1 by a to-many
        relationship
        """
        uuids = [uuid4().hex for _ in range(109)]
        obj = {
            'type': 'test',
            'id': '123',
            '_uuid': uuid4().hex,
            'relationships': {
                'many': {
                    'excellent': uuids
                }
            }
        }
        manys = [
            {
                'type': 'test2',
                'id': str(i),
                '_uuid': uuid,
                'attributes': {
                    'thing': f'thing_{i}'
                }
            }
            for i, uuid in enumerate(uuids)
        ]
        all_objects = [obj, *manys]
        parsed = ApiUpsertParser().parse(all_objects)
        assert len(parsed) == len(all_objects)
        parsed = sorted(parsed, key=lambda p: (p.type, p.id))
        parsed_obj_filters = [o for o in parsed if o.type == 'test']
        assert len(parsed_obj_filters) == 1
        # check the first object
        parsed_obj = parsed_obj_filters[0]
        # deliberately remove many
        expected = {
            'type': 'test',
            'id': '123',
            'attributes': {},
            'one': {},
        }
        observed = self.__dump_data_object(parsed_obj)
        del observed['many']
        assert expected == observed
        # check the other objects on the many end
        parsed_manys = [o for o in parsed if o.type == 'test2']
        assert len(parsed_manys) == 109
        expected = {
            str(i): {
                'type': 'test2',
                'id': str(i),
                'attributes': {
                    'thing': f'thing_{i}'
                },
                'one': {},
                'many': {}
            }
            for i in range(109)
        }
        observed = {
            o['id']: o for o in self.__dump_data_objects_list(parsed_manys)
        }
        assert expected == observed
        # check the objects are the same
        parsed_obj_manys = {
            o['id']: o for o in self.__dump_data_objects_list(
                parsed_obj.to_many_relationships['excellent']
            )
        }
        assert observed == parsed_obj_manys

    def test_both_relationship_complex(self):
        """
        Tests a complex of objects, with both kinds of relationships
        existing within
        """
        # TODO this!!!

    def __dump_data_object(
        self,
        data_object: DataObject
    ) -> Dict[str, Any]:
        return {
            'type': data_object.type,
            'id': data_object.id,
            'attributes': data_object.attributes,
            'one': data_object.to_one_relationships,
            'many': data_object.to_many_relationships
        }

    def __dump_data_objects_list(
        self,
        data_objects: List[DataObject]
    ) -> List[Dict[str, Any]]:
        return [
            self.__dump_data_object(d)
            for d in data_objects
        ]
