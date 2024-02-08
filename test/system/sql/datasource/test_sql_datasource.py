# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from tol.core import core_data_object
from tol.sql import create_sql_datasource
from tol.sql.sql_converter import TypeFunction

from .. import models


DB_URI = os.environ['DB_URI']


class TestCreateSqlDataSource:
    def test_get_by_id(self, session_factory, models_list):
        """With many corresponding models, both found and not found"""

        # add the objects
        session = session_factory()
        ids = ['200', '201', '202', '302']
        for id_ in ids:
            session.add(
                models.A(id=id_, string_column=f'the code is {id_}')
            )
        session.commit()
        session.close()

        # create the sql datasource (with default type function)
        sql_ds = create_sql_datasource(models_list, DB_URI)

        # setup the data object factory
        core_data_object(sql_ds)

        search_ids = [*ids, '404']  # add an ID that isn't in the DB

        # fetch by the id's
        data_objects = list(
            sql_ds.get_by_id('a', search_ids)
        )

        # 5 data objects, last is None
        assert len(data_objects) == 5
        assert data_objects[4] is None

        # go through the first 4 and assert they're correct
        for id_, data_object in zip(ids, data_objects[:-1]):
            assert data_object.type == 'a'
            assert data_object.id == id_
            assert data_object.attributes == {
                'string_column': f'the code is {id_}'
            }

    def test_get_list_page(self, session_factory, models_list):
        """Get a page of results, check the results and count"""

        # add the rows
        session = session_factory()
        for i in range(65, 72):  # A-G
            session.add(
                models.A(id=str(i), string_column=chr(i))
            )
        session.commit()
        session.close()

        # override type function
        type_function: TypeFunction = lambda m: f'type-{m.get_table_name()}'

        # create the sql datasource (with default type function)
        sql_ds = create_sql_datasource(
            models_list,
            DB_URI,
            type_function=type_function
        )

        # setup the data object factory
        core_data_object(sql_ds)

        # iterate through pages of 2
        for i in range(3):
            data_objects, count = sql_ds.get_list_page(
                'type-a',
                i + 1,  # page number starts from 1
                page_size=2
            )
            # count should always be 7
            assert count == 7
            # right pair of objects
            [first, second] = list(data_objects)
            for j, data_object in enumerate([first, second], start=i * 2):
                assert data_object.type == 'type-a'
                assert data_object.id == str(65 + j)
                assert data_object.attributes == {
                    'string_column': chr(65 + j)
                }

        # final page should have just 1 item
        data_objects, count = sql_ds.get_list_page('type-a', 4, page_size=2)
        # count the same
        assert count == 7
        # right object, and only one
        [final] = list(data_objects)
        assert final.type == 'type-a'
        assert final.id == '71'
        assert final.attributes == {'string_column': 'G'}

        # check the next few pages are empty
        for i in range(5, 9):
            data_objects, count = sql_ds.get_list_page('type-a', i, page_size=2)
            # count still the same
            assert count == 7
            # empty page
            assert len(list(data_objects)) == 0
