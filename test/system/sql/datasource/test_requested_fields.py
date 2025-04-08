# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from typing import Iterable

from tol.core import DataObject, core_data_object
from tol.sql import create_sql_datasource
from tol.sql.sql_converter import TypeFunction

from .. import models


DB_URI = os.environ['DB_URI']


class TestRequestedFields:
    """
    Specifying a `requested_fields` kwarg on the various operations
    within `SqlDataSource` fetches only those fields.
    """

    def test_single(self, session_factory, models_list):
        """Without relationships"""

        # add the objects
        session = session_factory()
        ids = list('abc')
        for i, id_ in enumerate(ids):
            session.add(
                models.B(
                    id_override=id_,
                    int_column=i,
                    another_string='exclude me!'
                )
            )
        session.commit()
        session.close()

        # create the sql datasource (with default type function)
        sql_ds = create_sql_datasource(models_list, DB_URI)
        core_data_object(sql_ds)

        def __assert_requested(iter_b: Iterable[DataObject]) -> None:
            for i, (b, letter) in enumerate(zip(iter_b, 'abc')):
                # requested fields are there
                assert b.id == letter
                assert b.int_column == i

        # `get_list()`
        iter_b = sql_ds.get_list('b', requested_fields=['int_column'])
        __assert_requested(iter_b)

        # `get_list_page()`
        page_b, count_b = sql_ds.get_list_page(
            'b',
            1,
            requested_fields=['int_column']
        )
        assert count_b == 3
        __assert_requested(page_b)

    def test_relations(self, session_factory, models_list):
        """With relationships"""

        # add the objects
        session = session_factory()
        session.add(
            models.R2(
                id='something comforting',
                funny_string='yes'
            )
        )
        session.add(
            models.R1(
                id_override='idk',
            )
        )
        session.add(
            models.R3(
                id='neither',
                another_string='look to the sky'
            )
        )
        session.commit()
        session.close()

        # create the sql datasource (with default type function)
        sql_ds = create_sql_datasource(models_list, DB_URI)
        core_data_object(sql_ds)

        def __assert_requested(iter_r3: Iterable[DataObject]) -> None:
            (r3,) = list(iter_r3)

            # meant to be there
            assert r3.id == 'neither'
            assert r3.funny_r1.id == 'idk'
            assert r3.funny_r1.r2_d2.id == 'something comforting'
            assert r3.funny_r1.r2_d2.funny_string == 'yes'

            # not meant to be there
            assert not r3.another_string

        # `get_list()`
        iter_r3 = sql_ds.get_list(
            'r3',
            requested_fields=['funny_r1.r2_d2.funny_string']
        )
        __assert_requested(iter_r3)

        # `get_list_page()`
        page_r3, count_r3 = sql_ds.get_list_page(
            'r3',
            1,
            requested_fields=['funny_r1.r2_d2.funny_string']
        )
        assert count_r3 == 1
        __assert_requested(page_r3)
