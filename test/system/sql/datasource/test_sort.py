# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.sql.database import DefaultDatabase
from tol.sql.sort import DefaultDatabaseSorter

from .. import models


class TestDefaultDatabaseSorter:

    def test_sort_ascending(self, session_factory, models_list):

        # add the models
        session = session_factory()
        for i in range(7):
            test_a = models.A(
                id=str(i),
                string_column=str(20 - i)
            )
            session.add(test_a)
        session.commit()
        session.close()

        db = DefaultDatabase(session_factory, models_list)

        sorter = DefaultDatabaseSorter('string_column')
        a_list = db.get_page('a', sort_by=sorter)
        # the difference is preserved
        for a in a_list:
            assert a.string_column == str(20 - int(a.id))
        # order is preserved
        string_columns = [int(a.string_column) for a in a_list]
        assert string_columns == list(range(14, 21))

    def test_sort_descending(self, session_factory, models_list):

        # add the models
        session = session_factory()
        for i in range(6):
            test_a = models.A(
                id=str(i),
                string_column=str(32 - i)
            )
            session.add(test_a)
        session.commit()
        session.close()

        db = DefaultDatabase(session_factory, models_list)

        sorter = DefaultDatabaseSorter('-string_column')
        a_list = db.get_page('a', sort_by=sorter)
        # the difference is preserved
        for a in a_list:
            assert a.string_column == str(32 - int(a.id))
        # order is preserved
        string_columns = [int(a.string_column) for a in a_list]
        assert string_columns == list(range(32, 26, -1))
