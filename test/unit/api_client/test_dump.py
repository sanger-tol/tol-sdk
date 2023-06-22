# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_client.dump import (
    DefaultObjectDumper,
    ObjectDumper,
    UpsertDumper
)
from tol.core import DataObject, core_data_object


CoreDataObject = core_data_object()  # noqa


class _ExampleObjectDumper(ObjectDumper):
    """Returns the count of one and many relations"""

    def dump(self, data_object: DataObject):
        ones_count = len(data_object.to_one_relationships)
        manys_count = sum([
            len(v) for v
            in data_object.to_many_relationships.values()
        ])
        return {
            'type': data_object.type,
            'id': data_object.id,
            'ones': ones_count,
            'manys': manys_count
        }


class TestUpsertDumper:
    def test_single_object(self):
        """Single object dumps correctly, considering only uuid"""
        d = CoreDataObject(
            'test',
            id_='123',
            data={
                'hype': 'train',
                'int': 4985
            }
        )
        observed = UpsertDumper(lambda: _ExampleObjectDumper()).dump([d])
        expected = {
            'data': [
                {
                    'type': 'test',
                    'id': '123',
                    'ones': 0,
                    'manys': 0
                }
            ]
        }
        assert observed == expected

    def test_several_one_relationships(self):
        """Several to-one relationships on the same object"""
        d = CoreDataObject('test')
        d_ones = [
            CoreDataObject(f'one_end-{"A" * i}', id_=str(i))
            for i in range(234)
        ]
        # set each to-one relationship on d
        for d_one in d_ones:
            setattr(d, d_one.type, d_one)
        expected_ones = [
            {
                'type': f'one_end-{"A" * i}',
                'id': str(i),
                'manys': 0,
                'ones': 0
            }
            for i in range(234)
        ]
        expected = {
            'data': [
                *expected_ones,
                {
                    'type': 'test',
                    'id': None,
                    'manys': 0,
                    'ones': 234
                }
            ]
        }
        observed = UpsertDumper(lambda: _ExampleObjectDumper()).dump([d, *d_ones])
        assert observed == expected

    def test_many_relationship(self):
        """One to-many relationship on an object"""
        d = CoreDataObject('test')
        d_manys = [
            CoreDataObject(
                'many',
                data={
                    'hype': 'train'
                }
            )
            for _ in range(23)
        ]
        d.manys = d_manys
        d_many2 = CoreDataObject('aaaaaaa')
        d.manys2 = [d_many2]
        expected_manys = [
            {
                'type': 'many',
                'id': None,
                'ones': 0,
                'manys': 0
            }
            for _ in range(23)
        ]
        expected = {
            'data': [
                {
                    'type': 'aaaaaaa',
                    'id': None,
                    'ones': 0,
                    'manys': 0
                },
                *expected_manys,
                {
                    'type': 'test',
                    'id': None,
                    'ones': 0,
                    'manys': 24
                }
            ]
        }
        observed = UpsertDumper(lambda: _ExampleObjectDumper()).dump([d, d_many2, *d_manys])
        assert observed == expected

    def test_mixed_relationships(self):
        """Several of both to-one and to-many relationships"""
        d = CoreDataObject('test')
        d_ones = [
            CoreDataObject(f'one_end-{"A" * i}', id_=str(i))
            for i in range(234)
        ]
        # set each to-one relationship on d
        for d_one in d_ones:
            setattr(d, d_one.type, d_one)
        expected_ones = [
            {
                'type': f'one_end-{"A" * i}',
                'id': str(i),
                'manys': 0,
                'ones': 0
            }
            for i in range(234)
        ]
        d_manys = [
            CoreDataObject(
                'many',
                data={
                    'hype': 'train'
                }
            )
            for _ in range(23)
        ]
        d.manys = d_manys
        many2 = CoreDataObject('aaaaaaa')
        d.manys2 = [many2]
        expected_manys = [
            {
                'type': 'many',
                'id': None,
                'ones': 0,
                'manys': 0
            }
            for _ in range(23)
        ]
        expected = {
            'data': [
                {
                    'type': 'aaaaaaa',
                    'id': None,
                    'ones': 0,
                    'manys': 0
                },
                *expected_manys,
                *expected_ones,
                {
                    'type': 'test',
                    'id': None,
                    'ones': 234,
                    'manys': 24
                }
            ]
        }
        observed = UpsertDumper(lambda: _ExampleObjectDumper()).dump(
            [d, many2, *d_ones, *d_manys]
        )
        assert observed == expected


class TestDefaultObjectDumper:
    def test_no_relationships(self):
        """No relationships means no uuids"""
        d = self.__tag_data_object(
            CoreDataObject(
                'test',
                id_='3948',
                data={
                    'yes': 'oui'
                }
            ),
            'abd'
        )
        expected = {
            'type': 'test',
            '_uuid': 'abd',
            'id': '3948',
            'attributes': {
                'yes': 'oui'
            }
        }
        observed = DefaultObjectDumper().dump(d)
        assert observed == expected

    def test_to_one_reference_chain(self):
        """
        With a long to-one reference chain, only the direct reference
        (just one hop) is considered
        """
        d_next = CoreDataObject('test')
        for i in range(101):
            d_next = self.__tag_data_object(
                CoreDataObject(f'test_{i}', {'prev': d_next}),
                f'the_uuid-is:{i}'
            )
        expected = {
            'type': 'test_100',
            '_uuid': 'the_uuid-is:100',
            'relationships': {
                'one': {
                    'prev': 'the_uuid-is:99'
                }
            }
        }
        observed = DefaultObjectDumper().dump(d_next)
        assert observed == expected

    def test_mixed_relationships(self):
        """Mix both to-one and to-many relationships"""
        d = self.__tag_data_object(
            CoreDataObject(
                'test',
                id_='3948',
                data={
                    'yes': 'oui'
                }
            ),
            'abd'
        )
        d.the_one_and_only = self.__tag_data_object(
            CoreDataObject(
                'me',
                id_='29'
            ),
            'hype'
        )
        d.entirely_too_many = [
            self.__tag_data_object(
                CoreDataObject(
                    'lol',
                    id_=str(i)
                ),
                str(i)
            )
            for i in range(32)
        ]
        many_uuids = [str(i) for i in range(32)]
        expected = {
            'type': 'test',
            '_uuid': 'abd',
            'id': '3948',
            'attributes': {
                'yes': 'oui'
            },
            'relationships': {
                'one': {
                    'the_one_and_only': 'hype'
                },
                'many': {
                    'entirely_too_many': many_uuids
                }
            }
        }
        observed = DefaultObjectDumper().dump(d)
        assert observed == expected

    def __tag_data_object(self, data_object: DataObject, _uuid: str) -> DataObject:
        """Adds a _uuid to a DataObject instance."""
        data_object._request_uuid = _uuid
        return data_object
