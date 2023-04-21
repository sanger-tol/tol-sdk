# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import (
    DataObject,
    TypedObjectDict
)


class TestTypedObjectDict:
    def test_add_one_object(self):
        u_dict = TypedObjectDict()
        d_object = DataObject(
            'test'
        )
        u_dict.add(d_object)

        assert len(u_dict.keys()) == 1
        assert u_dict['test'] == [d_object]

    def test_add_many_objects_one_type(self):
        u_dict = TypedObjectDict()
        d_objects = [
            DataObject(
                'test',
                {
                    'field': f'value_{i}'
                }
            )
            for i in range(100)
        ]
        for d in d_objects:
            u_dict.add(d)

        assert len(u_dict.keys()) == 1
        assert u_dict['test'] == d_objects

    def test_add_one_object_for_many_types(self):
        u_dict = TypedObjectDict()
        d_objects = [
            DataObject(
                f'test_{i}',
                {
                    'field': f'value_{i}'
                }
            )
            for i in range(100)
        ]
        u_dict.add_bulk(d_objects)

        expected = {
            d.type: [d]
            for d in d_objects
        }

        assert dict(u_dict) == expected
