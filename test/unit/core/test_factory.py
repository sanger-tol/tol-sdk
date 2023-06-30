# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable, List, Optional

import pytest

from tol.core import (
    DataObject,
    DataSource,
    core_data_object
)
from tol.core.abc import Relational
from tol.core.relationship import NotRelationalError, RelationshipConfig


class _MockDataSource1(DataSource):
    """A rather vaccuous implementation of DataSource"""

    @property
    def supported_types(self):
        return ['non-relational']

    def get_attribute_types(self, object_type: str):
        return {}


class _RelationalDataSource(DataSource, Relational):
    """
    Implements Relational

    a has a to-one relationship directed at b
    a has a to-many relationship directed at c
    """

    def __init__(self, b_id: str = None, c_ids: List[str] = None):
        self.__b_id = b_id
        self.__c_ids = c_ids
        self.__many_count = 0
        self.__one_count = 0

    @property
    def supported_types(self):
        return ['a', 'b', 'c']

    @property
    def many_count(self) -> int:
        return self.__many_count

    @property
    def one_count(self) -> int:
        return self.__one_count

    @property
    def relationship_config(self) -> Dict[str, RelationshipConfig]:
        return {
            'a': RelationshipConfig(
                to_one={'just_one_B': 'b'},
                to_many={'entirely-too_many_C-grades...': 'c'}
            )
        }

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Iterable[DataObject]:

        self.__many_count += 1

        return [
            self.data_object_factory(
                'c',
                id_=id_,
                data={'funny': 'A' * int(id_)}
            )
            for id_ in self.__c_ids
        ]

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ) -> Optional[DataObject]:

        self.__one_count += 1

        return self.data_object_factory(
            'b',
            id_=self.__b_id,
            data={
                'absolutely': 'not'
            }
        )

    def get_attribute_types(self, object_type: str):
        raise NotImplementedError()


class TestCoreDataObject:
    def test_data_object_returned(self):
        """returns a DataObject implementation"""

        result = core_data_object(_MockDataSource1({}))
        assert issubclass(result, DataObject)

    def test_data_source_given_factory(self):
        """
        A DataSource instance given to core_data_object is given a factory
        """

        ds = _MockDataSource1({})
        core_data_object(ds)
        assert ds.data_object_factory is not None

    def test_non_relational_error(self):
        """
        Trying to access relationships on a non-relational DataObject host
        raises an Exception
        """

        cdo = core_data_object(_MockDataSource1({}), _RelationalDataSource())

        # non-relational object raises exceptions
        data_object = cdo('non-relational')
        with pytest.raises(NotRelationalError):
            data_object.to_one_relationships
        with pytest.raises(NotRelationalError):
            data_object.to_many_relationships

        # relational object does not raise
        relational = cdo('a')
        one = relational.to_one_relationships
        many = relational.to_many_relationships

        # the collections.abc.Mapping methods work
        assert list(many) == ['entirely-too_many_C-grades...']
        assert len(many) == 1
        assert list(one) == ['just_one_B']
        assert len(one) == 1

    def test_get_bad_relationship(self):
        """
        both one and many relationships raise KeyError on bad relationship name
        """
        cdo = core_data_object(_MockDataSource1({}), _RelationalDataSource())
        source = cdo('a')

        # bad to-one
        with pytest.raises(KeyError):
            source.to_one_relationships['lol']

        # bad to-many
        with pytest.raises(KeyError):
            source.to_many_relationships['lol-but-many']

    def test_get_many(self):
        """to_many_relationships lazily loads and memoizes"""

        c_ids = [str(i) for i in range(23, 78, 3)]
        rel = _RelationalDataSource(c_ids=c_ids)
        cdo = core_data_object(_MockDataSource1({}), rel)
        source = cdo('a')
        many = source.to_many_relationships

        # nothing has been fetched yet
        assert rel.many_count == 0

        # get the many relationship once
        fetched_cs = many['entirely-too_many_C-grades...']
        # check they're right
        assert len(fetched_cs) == len(range(23, 78, 3))
        for i, c_object in enumerate(fetched_cs):
            assert c_object.type == 'c'
            id_ = 23 + 3 * i
            assert c_object.id == str(id_)
            assert c_object.attributes == {
                'funny': 'A' * id_
            }
        # check called just once
        assert rel.many_count == 1

        # get the many relationship again
        many['entirely-too_many_C-grades...']
        # it's still only called once
        assert rel.many_count == 1

    def test_get_one(self):
        """
        to_one relationships work on DefaultCoreDataObject and support:

        - lazy loading
        - memoisation
        - overwriting
        """

        b_id = 'hype'
        rel = _RelationalDataSource(b_id=b_id)
        cdo = core_data_object(_MockDataSource1({}), rel)
        source = cdo('a')
        one = source.to_one_relationships

        # nothing has been fetched yet
        assert rel.one_count == 0

        # get the relation
        rel_b = one['just_one_B']
        # check its right
        assert rel_b.type == 'b'
        assert rel_b.id == b_id
        assert rel_b.attributes == {'absolutely': 'not'}
        # only fetched once
        assert rel.one_count == 1

        # get it again
        one['just_one_B']
        # assert it's still only fetched once
        assert rel.one_count == 1

        # overwrite the relationship
        new_b = cdo('b', id_='new', data={'funny??': 'NOO'})
        source.just_one_B = new_b
        # get it again (should have the new value)
        assert one['just_one_B'] == new_b
        # assert it's still only fetched once
        assert rel.one_count == 1
        # check it's still right the other way
        assert source.to_one_relationships['just_one_B'] == new_b
