# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.core import DataSourceError
from tol.sql.database import DefaultDatabase

from .. import models


class TestDefaultDatabase:
    def test_count_none(self, session_factory, models_list, sess):
        """No rows -> count = 0"""

        db = DefaultDatabase(session_factory, models_list)
        count = db.count('a', sess)
        assert count == 0

    def test_count_with_added(self, session_factory, models_list, sess):
        # add the models
        session = session_factory()
        for i in range(7):
            test_a = models.A(id=str(i))
            session.add(test_a)
        session.commit()
        session.close()

        # get the count, assert its right
        db = DefaultDatabase(session_factory, models_list)
        count = db.count('a', sess)
        assert count == 7

    def test_get_to_one_relation_none(self, session_factory, models_list, sess):
        """instance_to_one_relations with no instance set"""

        # add an R1 without a to-one R2
        session = session_factory()
        session.add(models.R1(id_override='jape'))
        session.commit()
        session.close()

        # assert that getting its relation is None
        db = DefaultDatabase(session_factory, models_list)
        r2_relation = db.get_to_one_relation(
            'r1',
            'jape',
            'r2_d2',
            sess
        )
        assert r2_relation is None

    def test_get_to_one_relation_set(self, session_factory, models_list, sess):
        """instance_to_one_relations with one instance set"""
        # add an R1 alongside a to-one R2
        session = session_factory()
        session.add(
            models.R1(
                id_override='omni',
                r2_foreign_key='lol'
            )
        )
        session.add(models.R2(id='lol'))
        session.commit()
        session.close()

        # assert that getting its relation is not None
        db = DefaultDatabase(session_factory, models_list)
        r2_relation = db.get_to_one_relation(
            'r1',
            'omni',
            'r2_d2',
            sess
        )
        assert r2_relation is not None
        assert r2_relation.instance_id == 'lol'

    def test_get_to_many_relations_empty(self, session_factory, models_list, sess):
        """instance_to_many_relations with empty result"""

        # add an R1 without any R3's
        session = session_factory()
        session.add(models.R1(id_override='whatever'))
        session.commit()
        session.close()

        # assert that getting its many relation is empty
        db = DefaultDatabase(session_factory, models_list)
        r3_relations = db.get_to_many_relations(
            'r1',
            'whatever',
            'r3_plz',
            sess
        )
        assert list(r3_relations) == []

    def test_get_to_many_relations_set(self, session_factory, models_list, sess):
        """
        get_to_many_relations with a populated result.

        additionally, it returns an `Iterable` that can continue `next()`-ing
        after the `Iterator` is produced. (the session is not closed)
        """

        # add an R1 with 4 R3's
        session = session_factory()
        session.add(models.R1(id_override='neverending-hype'))
        for i in range(1, 5):
            session.add(
                models.R3(
                    id=str(i),
                    ur_r1_id='neverending-hype'
                )
            )
        session.commit()
        session.close()

        # assert that there are 4 correct relations
        db = DefaultDatabase(session_factory, models_list)
        r3_relations = list(
            db.get_to_many_relations(
                'r1',
                'neverending-hype',
                'r3_plz',
                sess
            )
        )
        # correct length
        assert len(r3_relations) == 4
        # correct order
        for i, rel in enumerate(r3_relations, start=1):
            assert rel.instance_id == str(i)

    def test_delete(self, session_factory, models_list, sess):
        """Delete works when given a good tablename and instance-ID"""

        # add an "A"
        session = session_factory()
        session.add(
            models.A(id='what are you going to do, delete me?')
        )
        session.commit()
        session.close()

        # delete the "A" using a DefaultDatabase
        db = DefaultDatabase(session_factory, models_list)
        db.delete(
            'a',
            'what are you going to do, delete me?',
            sess
        )

        # confirm the "A" is deleted
        session = session_factory()
        existing_a_s = session.query(models.A).all()
        session.close()
        assert len(existing_a_s) == 0

    def test_upsert_not_existing(self, session_factory, models_list, sess):
        """Upsert on non-existant row causes an insert"""

        # add an "A"
        session = session_factory()
        session.add(
            models.A(
                id='101',
                string_column='update me!'
            )
        )
        session.commit()
        session.close()

        # upsert a new version
        db = DefaultDatabase(session_factory, models_list)
        db.upsert(
            models.A(
                id='101',
                string_column='consider yourself updated'
            ),
            sess
        )

        # confirm the "A" is updated
        session = session_factory()
        existing_a = session.query(models.A).one_or_none()
        assert existing_a is not None
        assert existing_a.id == '101'
        assert existing_a.string_column == (
            'consider yourself updated'
        )
        session.close()

    def test_insert_existing(self, session_factory, models_list, sess):
        """Insert on existing model -> raises `DataSourceError`"""

        session = session_factory()
        session.add(
            models.A(
                id='101',
                string_column='please do not try to update me'
            )
        )
        session.commit()
        session.close()

        db = DefaultDatabase(session_factory, models_list)

        # insert a duplicate
        with pytest.raises(DataSourceError):
            db.insert(
                models.A(
                    id='101',
                    string_column='I am invincible'
                ),
                sess
            )

    def test_insert_not_existing(self, session_factory, models_list, sess):
        """Insert on not previously existing model -> all good"""

        db = DefaultDatabase(session_factory, models_list)
        db.insert(
            models.A(
                id='101',
                string_column='I am invincible'
            ),
            sess
        )

        # confirm the "A" is inserted
        session = session_factory()
        existing_a = session.query(models.A).one_or_none()
        assert existing_a is not None
        assert existing_a.id == '101'
        assert existing_a.string_column == (
            'I am invincible'
        )
        session.close()

    def test_upsert_on_existing(self, session_factory, models_list, sess):
        """Upsert on existing row causes an update"""

        # upsert a new version
        db = DefaultDatabase(session_factory, models_list)
        db.upsert(
            models.A(
                id='303',
                string_column='consider yourself inserted'
            ),
            sess
        )

        # confirm the "A" is inserted
        session = session_factory()
        existing_a = session.query(models.A).one_or_none()
        assert existing_a is not None
        assert existing_a.id == '303'
        assert existing_a.string_column == (
            'consider yourself inserted'
        )
        session.close()
