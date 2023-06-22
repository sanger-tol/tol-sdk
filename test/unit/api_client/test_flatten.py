# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable, List

from tol.api_client.flatten import Flattener
from tol.core import DataObject, core_data_object


CoreDataObject = core_data_object()  # noqa


class TestFlattener:
    def test_single_object(self):
        """1 object produces 1 object"""
        d = CoreDataObject('test', {'hype': 'train'})
        flattened = Flattener().flatten([d])
        assert flattened == [d]

    def test_many_objects_mutltiple_types(self):
        """Several already flat objects produce the same number"""
        ds = [
            CoreDataObject(f'test_{i}')
            for i in range(102)
        ]
        flattened = Flattener().flatten(ds)
        self.__assert_iterables_equal(
            flattened,
            ds
        )

    def test_to_one_reference_with_duplicate(self):
        """
        A to-one reference with the target added separately as well
        """
        d1 = CoreDataObject('A')
        d2 = CoreDataObject('B', {'a': d1})
        flattened = Flattener().flatten([d2, d1])
        self.__assert_iterables_equal(
            flattened,
            [d1, d2]
        )

    def test_to_one_reference_chain(self):
        """
        Several to-one references forming a linked list
        """
        d_end = CoreDataObject('test')
        ds = [d_end]
        d_next = d_end
        for i in range(101):
            d_next = CoreDataObject(f'test_{i}', {'prev': d_next})
            ds.append(d_next)
        flattened = Flattener().flatten([d_next])
        self.__assert_iterables_equal(
            flattened,
            ds
        )

    def test_to_many_references(self):
        """
        Several to-many relationships on one object
        """
        d = CoreDataObject('test')
        d_many1 = [CoreDataObject('many1')]
        d_many2 = [
            CoreDataObject('many2', id_=str(i))
            for i in range(44)
        ]
        d.many1 = d_many1
        d.many2 = d_many2
        flattened = Flattener().flatten([d] + d_many2)
        self.__assert_iterables_equal(
            flattened,
            [d] + d_many1 + d_many2
        )

    def test_both_to_one_to_many_references(self):
        """
        Combine to-one and to-many relationships on the same object
        """
        d1 = CoreDataObject('A')
        d2 = CoreDataObject('B', {'a': d1})  # one end
        d3 = CoreDataObject('C')  # many end
        d2.c = [d3]
        flattened = Flattener().flatten([d2])
        self.__assert_iterables_equal(
            flattened,
            [d1, d2, d3]
        )

    def test_circular_reference(self):
        """
        A circular reference should not cause infinite recursion
        """
        a = CoreDataObject('a')
        b = CoreDataObject('b')
        a.b = b
        b.many_a = [a]
        flattened = Flattener().flatten([a, b])
        self.__assert_iterables_equal(
            flattened,
            [a, b]
        )

    def __sort_by_type(self, data_objects: Iterable[DataObject]) -> List[DataObject]:
        return sorted(
            data_objects,
            key=lambda d: (d.type, d._request_uuid)  # this also ensures every object has a UUID
        )

    def __assert_iterables_equal(self, i1: Iterable[DataObject], i2: Iterable[DataObject]):
        s1 = self.__sort_by_type(i1)
        s2 = self.__sort_by_type(i2)
        assert s1 == s2
