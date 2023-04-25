# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_client.api_object_serializer import ApiDataSerializer
from tol.core import CoreDataObject


class TestApiDataObjectSerializer:
    def test_single_object(self):
        data_object = CoreDataObject(
            'test',
            {
                'test1': 'hype',
                'another_test': 'waiting for this train'
            }
        )
        expected = [
            {
                'type': 'test',
                '_uuid': data_object._internal_uuid,
                'attributes': {
                    'test1': 'hype',
                    'another_test': 'waiting for this train'
                }
            }
        ]
        result = ApiDataSerializer().dump([data_object])
        assert result == expected

    def test_many_objects_mutltiple_types(self):
        data_objects = [
            CoreDataObject(
                f'test_{i}',
                {
                    'the_id': i
                }
            )
            for i in range(2389)
        ]
        uuids = [
            d._internal_uuid
            for d in data_objects
        ]
        unsorted = [
            {
                'type': f'test_{i}',
                '_uuid': uuid,
                'attributes': {
                    'the_id': i
                }
            }
            for i, uuid in enumerate(uuids)
        ]
        expected = sorted(
            unsorted,
            key=lambda d: d['type']
        )
        result = ApiDataSerializer().dump(data_objects)
        assert result == expected

    def test_to_one_reference(self):
        a = CoreDataObject('a')
        b = CoreDataObject('b')
        # add in a known id
        b.id = 'test_id'
        b.a_entry = a
        expected = [
            {
                'type': 'a',
                '_uuid': a._internal_uuid
            },
            {
                'type': 'b',
                'id': 'test_id',
                '_uuid': b._internal_uuid,
                'relationships': {
                    'one': {
                        'a_entry': a._internal_uuid
                    }
                }
            }
        ]
        result = ApiDataSerializer().dump([b])
        assert expected == result

    def test_to_one_reference_removes_duplicate(self):
        a = CoreDataObject('a')
        b = CoreDataObject('b')
        b.a_entry = a
        expected = [
            {
                'type': 'a',
                '_uuid': a._internal_uuid
            },
            {
                'type': 'b',
                '_uuid': b._internal_uuid,
                'relationships': {
                    'one': {
                        'a_entry': a._internal_uuid
                    }
                }
            }
        ]
        # this time add them both, even though b already has a
        result = ApiDataSerializer().dump([a, b])
        assert expected == result

    def test_to_one_reference_chain(self):
        data_objects = [
            CoreDataObject(
                f'test_{i}',
                {
                    'the_id': 1000000 - i
                }
            )
            for i in range(238)
        ]
        # build the to-one reference chain
        for i, data_object in enumerate(data_objects):
            if i == 0:
                continue
            previous = data_objects[i - 1]
            data_object.previous = previous
        uuids = [d._internal_uuid for d in data_objects]
        unsorted = [
            {
                'type': f'test_{i}',
                '_uuid': uuid,
                'attributes': {
                    'the_id': 1000000 - i
                },
                'relationships': {
                    'one': {
                        'previous': (
                            uuids[i - 1] if i > 0 else None
                        )
                    }
                }
            }
            for i, uuid in enumerate(uuids)
        ]
        # the first one does not have a previous
        del unsorted[0]['relationships']
        # sort by type
        expected = sorted(
            unsorted,
            key=lambda d: d['type']
        )
        result = ApiDataSerializer().dump([data_objects[-1]])
        assert result == expected

    def test_to_many_references(self):
        a = CoreDataObject('a')
        many_b = [
            CoreDataObject(
                'b',
                {
                    'id_stuff': i
                }
            )
            for i in range(348)
        ]
        a.many_b = many_b
        uuids = [b._internal_uuid for b in many_b]
        expected = [
            {
                'type': 'a',
                '_uuid': a._internal_uuid,
                'relationships': {
                    'many': {
                        'many_b': uuids
                    }
                }
            },
            *[
                {
                    'type': 'b',
                    '_uuid': b._internal_uuid,
                    'attributes': {
                        'id_stuff': i
                    }
                }
                for i, b in enumerate(many_b)
            ]
        ]
        result = ApiDataSerializer().dump([a])
        assert result == expected

    def test_both_to_one_to_many_references(self):
        a = CoreDataObject('a')
        many_b = [
            CoreDataObject(
                'b',
                {
                    'id_stuff': i
                }
            )
            for i in range(348)
        ]
        c = CoreDataObject('c')
        a.many_b = many_b
        a.one_c = c
        uuids = [b._internal_uuid for b in many_b]
        expected = [
            {
                'type': 'a',
                '_uuid': a._internal_uuid,
                'relationships': {
                    'one': {
                        'one_c': c._internal_uuid,
                    },
                    'many': {
                        'many_b': uuids
                    }
                }
            },
            *[
                {
                    'type': 'b',
                    '_uuid': b._internal_uuid,
                    'attributes': {
                        'id_stuff': i
                    }
                }
                for i, b in enumerate(many_b)
            ],
            {
                'type': 'c',
                '_uuid': c._internal_uuid
            }
        ]
        result = ApiDataSerializer().dump([a])
        assert result == expected

    def test_circular_reference(self):
        """
        A circular reference should not cause infinite recursion
        """
        a = CoreDataObject('a')
        b = CoreDataObject('b')
        a.b = b
        b.many_a = [a]
        expected = [
            {
                'type': 'a',
                '_uuid': a._internal_uuid,
                'relationships': {
                    'one': {
                        'b': b._internal_uuid
                    }
                }
            },
            {
                'type': 'b',
                '_uuid': b._internal_uuid,
                'relationships': {
                    'many': {
                        'many_a': [
                            a._internal_uuid
                        ]
                    }
                }
            }
        ]
        result1 = ApiDataSerializer().dump([a])
        assert result1 == expected
        result2 = ApiDataSerializer().dump([b])
        assert result2 == expected
        result3 = ApiDataSerializer().dump([a, b])
        assert result3 == expected
        result4 = ApiDataSerializer().dump([b, a])
        assert result4 == expected
