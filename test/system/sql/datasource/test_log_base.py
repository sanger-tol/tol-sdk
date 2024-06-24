# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.sql.database import DefaultDatabase

from .. import models


class TestLogBase:
    """
    Tests `LogBase` using a real `Database` instance.
    """

    def test_first_upsert(self, session_factory, models_list, sess):
        """
        `modified_at` and `modified_by` are set on first
        `Database().upsert()`
        """

        db = DefaultDatabase(session_factory, models_list)

        model = models.C(id_override='I am an override')
        db.upsert(model, sess, user_id='101')

        fetched: models.C = db.get_by_id('c', 'I am an override', sess)

        assert fetched.id_override == 'I am an override'
        assert fetched.string_column is None
        assert fetched.modified_at is not None
        assert fetched.modified_by == '101'

    def test_second_upsert(self, session_factory, models_list, sess):
        """
        `Database().upsert()` sets `modified_at` and `modified_by`
        on a previously existing `LogBase` instance
        """

        db = DefaultDatabase(session_factory, models_list)

        model = models.C(id_override='I am an override')
        db.upsert(model, sess, user_id='101')

        fetched: models.C = db.get_by_id('c', 'I am an override', sess)

        assert fetched.id_override == 'I am an override'
        assert fetched.string_column is None
        assert fetched.modified_at is not None
        assert fetched.modified_by == '101'

        second_model = models.C(
            id_override='I am an override',
            string_column='I am now set! :)'
        )
        db.upsert(second_model, sess, user_id='202')  # different `user_id`

        fetched_second: models.C = db.get_by_id('c', 'I am an override', sess)

        assert fetched_second.id_override == 'I am an override'
        assert fetched_second.string_column == 'I am now set! :)'
        assert fetched_second.modified_at is not None
        assert fetched_second.modified_by == '202'

    def test_delete(self, session_factory, models_list, sess):
        """`Database().delete()` is possible for a `LogBase` instance"""

        db = DefaultDatabase(session_factory, models_list)

        model = models.C(id_override='I am an override')

        db.upsert(model, sess, user_id='101')

        db.delete('c', 'I am an override', sess, user_id='101')  # this isn't stored
