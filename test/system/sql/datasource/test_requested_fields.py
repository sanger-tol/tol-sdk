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
        """Test a model without relationships"""

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

        def __assert_required(iter_b: Iterable[DataObject]) -> None:
            for i, (b, letter) in enumerate(zip(iter_b, 'abc')):
                # required fields are there
                assert b.id == letter
                assert b.int_column == i

                # others are not
                assert not b.another_string

        # `get_list()`
        iter_b = sql_ds.get_list('b', requested_fields=['int_column'])
        __assert_required(iter_b)

        # `get_list_page()`
        page_b, count_b = sql_ds.get_list_page(
            'b',
            requested_fields=['int_column']
        )
        assert count_b == 3
        __assert_required(page_b)
