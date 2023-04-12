# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataObject
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
                'attributes': {
                    'test1': 'hype',
                    'another_test': 'waiting for this train'
                }
            }
        ]
        result = serializer.dump([data_object])
        assert result == expected

    def test_many_objects_same_type(self):
        pass

    def test_to_one_reference(self):
        pass

    def test_to_one_reference_chain(self):
        pass

    def test_to_many_references(self):
        pass

    def test_both_to_one_to_many_references(self):
        pass
