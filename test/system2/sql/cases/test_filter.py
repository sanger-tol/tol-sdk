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
        evens = db.get_list('a', filters=even_filter)
        for i, even in enumerate(evens):
            assert even.instance_id == str(i * 2)
            assert even.instance_attributes == {'string_column': 'even'}

        # check the odds [1, 3, 5]
        odd_filter = DefaultDatabaseFilter(
            DataSourceFilter(exact={'string_column': 'odd'})
        )
        count = db.count('a', filters=odd_filter)
        assert count == 3
        odds = db.get_list('a', filters=odd_filter)
        for i, odd in enumerate(odds):
            assert odd.instance_id == str(i * 2 + 1)
            assert odd.instance_attributes == {'string_column': 'odd'}
