# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

import pytest

from tol.benchling import BenchlingDataSource
from tol.core import DataSourceConfig, core_data_object

from .utils import against_types


@pytest.fixture(scope='module')
def ds_config() -> DataSourceConfig:
    return {
        'url': os.environ['BENCHLING_URL'],
        'api_key': os.environ['BENCHLING_API_KEY'],
        'registry_id': os.environ['BENCHLING_REGISTRY_ID'],
        'project_id': os.environ['BENCHLING_PROJECT'],
        'folder_id': os.environ['BENCHLING_FOLDER'],
    }


@pytest.fixture
def benchling_ds(
    ds_config: DataSourceConfig
) -> BenchlingDataSource:

    ds = BenchlingDataSource(
        ds_config
    )
    core_data_object(ds)

    return ds


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
    def test_one(
        self,
        benchling_ds: BenchlingDataSource,
        object_type: str
    ) -> None:
        """
        Inserts a single `DataObject` of specified type,
        confirms its there, and updates, confirms changes.
        """

        # create the object
        obj = benchling_ds.data_object_factory(
            object_type
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
    def test_many(
        self,
        benchling_ds: BenchlingDataSource,
        object_type: str
    ) -> None:
        """
        Inserts several `DataObject` instances of specified type,
        confirms they are present there, and updates, confirms
        changes.
        """

        # get the key of a `str` field
        str_key = self.__find_string_key(
            object_type,
            benchling_ds
        )

        # create the objects
        objs = [
            benchling_ds.data_object_factory(
                object_type,
                attributes={
                    str_key: 'A' * i
                }
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
            if v == 'str':
                return k

        raise Exception('no `str` key was found.')
