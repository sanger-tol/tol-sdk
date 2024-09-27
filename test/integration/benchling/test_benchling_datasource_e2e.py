# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import datetime

from tol.benchling import BenchlingDataSource
from tol.sources.benchling import benchling

from .utils import against_types


class TestBenchlingDataSourceE2E:
    """
    Tests `BenchlingDataSource` against a
    real Benchling instance.

    These functions operate only at the
    `DataSource` layer, using only
    standard `Operator` methods, and only confirm
    existence/non-existence.
    """

    @against_types(['tissue'])
    def test_one(self, object_type: str) -> None:
        """
        Inserts a single `DataObject` of specified type,
        confirms its there, and updates, confirms changes.
        """

        benchling_ds = benchling()

        # create the object
        obj = self.__create_test_object(
            object_type,
            benchling_ds,
            string_value='A'
        )

        # insert it
        res = list(
            benchling_ds.insert(
                object_type,
                [obj]
            )
        )

        # there can be only one
        assert len(res) == 1

        # get its new ID
        id_ = res[0].id

        # update a `str` attribute
        str_key = self.__find_string_key(
            object_type,
            benchling_ds
        )
        res = benchling_ds.update(
            object_type,
            [
                (
                    id_,
                    {
                        str_key: 'updated :)'
                    }
                )
            ]
        )

        assert len(res) == 1

        # assert everything is right (and `str` key is updated)
        assert res[0].type == object_type
        assert res[0].id == id_
        str_val = getattr(res[0], str_key)
        assert str_val == 'updated :)'

        # get it back
        new_obj = benchling_ds.get_one(
            object_type,
            id_
        )

        # assert everything is right (and `str` key is updated)
        assert new_obj.type == object_type
        assert new_obj.id == id_
        str_val = getattr(new_obj, str_key)
        assert str_val == 'updated :)'

    @against_types(['tissue'])
    def test_many(self, object_type: str) -> None:
        """
        Inserts several `DataObject` instances of specified type,
        confirms they are present there, and updates, confirms
        changes.
        """

        benchling_ds = benchling()

        # get the key of a `str` field
        str_key = self.__find_string_key(
            object_type,
            benchling_ds
        )

        # create the objects
        objs = [
            self.__create_test_object(
                object_type,
                benchling_ds,
                string_value='A' * i
            )
            for i in range(1, 4)
        ]

        # insert them
        res = list(
            benchling_ds.insert(
                object_type,
                objs
            )
        )

        # there should be 3
        assert len(res) == 3

        # they all have the right value for `str_key`
        for i, obj in enumerate(res, start=1):
            str_val = getattr(obj, str_key)
            assert str_val == 'A' * i

        # get their new ID's
        ids = [
            r.id for r in res
        ]

        # update each `str` attribute
        benchling_ds.update(
            object_type,
            [
                (
                    id_,
                    {
                        str_key: 'CBA' * i
                    }
                )
                for i, id_ in enumerate(ids, start=2)
            ]
        )

        # get them back
        new_objs = list(
            benchling_ds.get_by_id(
                object_type,
                ids
            )
        )

        # assert everything is right (and `str` key is updated)
        for i, (id_, new_obj) in enumerate(zip(ids, new_objs), start=2):
            assert new_obj.type == object_type
            assert new_obj.id == id_

            str_val = getattr(new_obj, str_key)
            assert str_val == 'CBA' * i

    def __find_string_key(
        self,
        object_type: str,
        benchling_ds: BenchlingDataSource
    ) -> str:
        """Finds an `attribute` key that is a string"""

        attribute_types = benchling_ds.attribute_types[object_type]

        for k, v in attribute_types.items():
            if v == 'str' and benchling_ds.entities[object_type][k]['required']:
                return k

        raise Exception('no `str` key was found.')

    def __create_test_object(
        self,
        object_type: str,
        benchling_ds: BenchlingDataSource,
        string_value: str = 'test',
        int_value: int = 1,
        float_value: float = 1.0,
        datetime_value: datetime.datetime = datetime.datetime(2021, 1, 1)
    ) -> str:
        """Creates test data for an example object"""
        atts = {}
        for att in benchling_ds.attribute_types[object_type]:
            # Easy way to avoid computed fields
            if not benchling_ds.entities[object_type][att]['required']:
                continue
            if benchling_ds.entities[object_type][att]['benchling_type'] == 'text':
                atts[att] = string_value
            if benchling_ds.entities[object_type][att]['benchling_type'] == 'integer':
                atts[att] = int_value
            if benchling_ds.entities[object_type][att]['benchling_type'] == 'float':
                atts[att] = float_value
            if benchling_ds.entities[object_type][att]['benchling_type'] == 'date':
                atts[att] = datetime_value
            if benchling_ds.entities[object_type][att]['benchling_type'] == 'dropdown':
                attribute_values = benchling_ds.get_attribute_value_options(object_type, att)
                atts[att] = next(iter(attribute_values.values()))
        return benchling_ds.data_object_factory(
            object_type,
            None,
            attributes=atts
        )
