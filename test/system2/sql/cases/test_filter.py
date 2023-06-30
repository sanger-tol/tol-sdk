# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter
from tol.sql.database import DefaultDatabase
from tol.sql.filter import DefaultDatabaseFilter

from .. import models
from ..base_case import DatabaseTestCase, models_list, session_factory


class TestDefaultDatabaseFilter(DatabaseTestCase):

    def test_exact_filter(self):
        """Exact filtering only returns the correct rows"""

        # add the models
        session = session_factory()
        for i in range(7):
            test_a = models.A(
                id=str(i),
                string_column='even' if i % 2 == 0 else 'odd'
            )
            session.add(test_a)
        session.commit()
        session.close()

        db = DefaultDatabase(session_factory, models_list)

        # check the evens [0, 2, 4, 6]
        even_filter = DefaultDatabaseFilter(
            DataSourceFilter(exact={'string_column': 'even'})
        )
        count = db.count('a', filters=even_filter)
        assert count == 4
        evens = db.get_page('a', filters=even_filter)
        for i, even in enumerate(evens):
            assert even.instance_id == str(i * 2)
            assert even.instance_attributes == {'string_column': 'even'}

        # check the odds [1, 3, 5]
        odd_filter = DefaultDatabaseFilter(
            DataSourceFilter(exact={'string_column': 'odd'})
        )
        count = db.count('a', filters=odd_filter)
        assert count == 3
        odds = db.get_page('a', filters=odd_filter)
        for i, odd in enumerate(odds):
            assert odd.instance_id == str(i * 2 + 1)
            assert odd.instance_attributes == {'string_column': 'odd'}

    def test_all_filters(self):
        """
        4 filters on 5 extant rows - each removes a different one - the db should fetch
        the only row that matches all 4.
        """

        session = session_factory()
        rows = [
            models.B(id_override='2', int_column=1, another_string='match'),  # range
            models.B(id_override='1', int_column=2, another_string='match'),  # contains
            models.B(id_override='23', int_column=3, another_string='match'),
            models.B(id_override='24', int_column=4, another_string='match'),  # list
            models.B(id_override='25', int_column=5, another_string='NO MATCH!!!!')  # exact
        ]
        for row in rows:
            session.add(row)
        session.commit()
        session.close()

        db = DefaultDatabase(session_factory, models_list)

        ds_filter = DataSourceFilter(
            exact={'another_string': 'match'},
            contains={'id': '2'},
            in_list={
                'id': ['1', '2', '23', '25', '81293']  # end with non present number just for fun
            },
            range={'int_column': {'from': 2, 'to': 100}}  # spill over on right side
        )
        db_filter = DefaultDatabaseFilter(ds_filter)

        # there can be only one
        count = db.count('b', filters=db_filter)
        assert count == 1

        # check it's the right one
        fetched = list(db.get_page('b', filters=db_filter))[0]
        assert fetched.instance_id == '23'
        assert fetched.instance_attributes == {
            'int_column': 3,
            'another_string': 'match'
        }
