# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.sql.database import DefaultDatabase

from .. import models
from ..base_case import DatabaseTestCase, models_list, session_factory


class TestDefaultDatabase(DatabaseTestCase):
    def test_count_none(self):
        """No rows -> count = 0"""

        db = DefaultDatabase(session_factory, models_list)
        count = db.count('a')
        assert count == 0

    def test_count_with_added(self):
        # add the models
        session = session_factory()
        for i in range(7):
            test_a = models.A(id=str(i))
            session.add(test_a)
        session.commit()
        session.close()

        # get the count, assert its right
        db = DefaultDatabase(session_factory, models_list)
        count = db.count('a')
        assert count == 7
