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

    def test_get_to_one_relation_none(self):
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
            'r2_d2'
        )
        assert r2_relation is None

    def test_get_to_one_relation_set(self):
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
            'r2_d2'
        )
        assert r2_relation is not None
        assert r2_relation.instance_id == 'lol'

    def test_get_to_many_relations_empty(self):
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
            'r3_plz'
        )
        assert list(r3_relations) == []

    def test_get_to_many_relations_set(self):
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
                'r3_plz'
            )
        )
        # correct length
        assert len(r3_relations) == 4
        # correct order
        for i, rel in enumerate(r3_relations, start=1):
            assert rel.instance_id == str(i)
