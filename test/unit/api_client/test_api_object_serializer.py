# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject, data_object
from tol.api_client.api_object_serializer import ApiDataObjectSerializer


serializer = ApiDataObjectSerializer()


class TestApiDataObjectSerializer:
    def test_single_object(self):
        data_object = DataObject(
            'test',
            {
                'test1': 'hype',
                'another_test': 'waiting for this train'
            }
        )
        expected = [
            {
                'type': 'test',
                '_uuid': data_object._request_internal_uuid,
                'attributes': {
                    'test1': 'hype',
                    'another_test': 'waiting for this train'
                }
            }
        ]
        result = serializer.dump([data_object])
        assert result == expected

    def test_many_objects_mutltiple_types(self):
        data_objects = [
            DataObject(
                f'test_{i}',
                {
                    'the_id': i
                }
            )
            for i in range(2389)
        ]
        uuids = [
            d._request_internal_uuid
            for d in data_objects
        ]
        expected = [
            {
                'type': f'test_{i}',
                '_uuid': uuid,
                'attributes': {
                    'the_id': i
                }
            }
            for i, uuid in enumerate(uuids)
        ]
        result = serializer.dump(data_objects)
        assert result == expected

    def test_to_one_reference(self):
        a = DataObject('a')
        b = DataObject('b')
        b.a_entry = a
        expected = [
            {
                'type': a,
                '_uuid': a._request_internal_uuid
            },
            {
                'type': b,
                '_uuid': b._request_internal_uuid,
                'relationships': {
                    'one': {
                        'a_entry': a._request_internal_uuid
                    }
                }
            }
        ]
        result = serializer.dump([b])
        assert expected == result

    def test_to_one_reference_removes_duplicate(self):
        a = DataObject('a')
        b = DataObject('b')
        b.a_entry = a
        expected = [
            {
                'type': a,
                '_uuid': a._request_internal_uuid
            },
            {
                'type': b,
                '_uuid': b._request_internal_uuid,
                'relationships': {
                    'one': {
                        'a_entry': a._request_internal_uuid
                    }
                }
            }
        ]
        # this time add them both, even though b already has a
        result = serializer.dump([a, b])
        assert expected == result

    def test_to_one_reference_chain(self):
        pass

    def test_to_many_references(self):
        pass

    def test_both_to_one_to_many_references(self):
        pass
