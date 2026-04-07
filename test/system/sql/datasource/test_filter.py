# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from pytest import fixture

from tol.core import DataSourceFilter
from tol.core.datasource_filter import AndFilter
from tol.sql.database import DefaultDatabase
from tol.sql.filter import DatabaseFilter, DefaultDatabaseFilter

from .. import models


@fixture(scope='module')
def type_tablename_dict(models_list) -> dict[str, str]:
    return {
        m.__tablename__: m.__tablename__ for m in models_list
    }


class TestDefaultDatabaseFilter:

    def test_exact_filter(self, session_factory, models_list, type_tablename_dict, sess):
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
        count = db.count('a', sess, filters=even_filter)
        assert count == 4
        evens = db.get_page('a', sess, filters=even_filter)
        for i, even in enumerate(evens):
            assert even.instance_id == str(i * 2)
            assert even.instance_attributes == {'string_column': 'even'}

        # check the odds [1, 3, 5]
        odd_filter = DefaultDatabaseFilter(
            DataSourceFilter(exact={'string_column': 'odd'})
        )
        count = db.count('a', sess, filters=odd_filter)
        assert count == 3
        odds = db.get_page('a', sess, filters=odd_filter)
        for i, odd in enumerate(odds):
            assert odd.instance_id == str(i * 2 + 1)
            assert odd.instance_attributes == {'string_column': 'odd'}

    def test_multi_level_relations_filter(self, session_factory, models_list, sess):
        """Multiple level query returns row"""

        # Store R3 -> R1 -> R2 chain of objects
        session = session_factory()
        session.add(
            models.R3(
                id='an-r3-id',
                funny_r1=models.R1(
                    id_override='an-r1-id',
                    r2_d2=models.R2(
                        id='an-r2-id',
                    ),
                ),
            )
        )
        session.commit()
        session.close()

        deep_filt = DefaultDatabaseFilter(
            DataSourceFilter(
                exact={'funny_r1.r2_d2.id': 'an-r2-id'},
            )
        )

        # Fetch the R3 object by ID of R2 object
        db = DefaultDatabase(session_factory, models_list)
        count = db.count('r3', sess, filters=deep_filt)
        assert count == 1
        (r3_obj,) = db.get_page('r3', sess, filters=deep_filt)
        assert r3_obj.id == 'an-r3-id'

    def test_fetch_null_relatoinship(self, session_factory, models_list, sess):
        # Store R3 -> R1 -> R2 chain of objects
        session = session_factory()
        session.add(
            models.R3(
                id='r3-1',
                funny_r1=models.R1(
                    id_override='r1-id',
                ),
            )
        )
        session.add(
            models.R3(
                id='r3-2',
                funny_r1=None,
            )
        )
        session.commit()
        session.close()

        db = DefaultDatabase(session_factory, models_list)
        fun = DefaultDatabaseFilter(
            DataSourceFilter(
                and_={
                    'funny_r1.id': {
                        'exists': {},
                    },
                }
            )
        )
        fun1_list = list(db.get_page('r3', sess, filters=fun))
        assert len(fun1_list) == 1
        assert fun1_list[0].id == 'r3-1'

        no_fun = DefaultDatabaseFilter(
            DataSourceFilter(
                and_={
                    'funny_r1.id': {
                        'exists': {'negate': True},
                    },
                }
            )
        )
        fun2_list = list(db.get_page('r3', sess, filters=no_fun))
        assert len(fun2_list) == 1
        assert fun2_list[0].id == 'r3-2'

    def test_all_filters(self, session_factory, models_list, type_tablename_dict, sess):
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
        count = db.count('b', sess, filters=db_filter)
        assert count == 1

        # check it's the right one
        fetched = list(db.get_page('b', sess, filters=db_filter))[0]
        assert fetched.instance_id == '23'
        assert fetched.instance_attributes == {
            'int_column': 3,
            'another_string': 'match'
        }

    def test_and_(self, session_factory, models_list, type_tablename_dict, sess):
        """
        `DefaultDatabaseFilter().filter()` using several `and_` terms.
        """

        session = session_factory()
        rows = [
            models.B(id_override='2', int_column=1, another_string='match'),
            models.B(id_override='1', int_column=2, another_string='match'),
            models.B(id_override='23', int_column=3),
            models.B(id_override='24', int_column=4, another_string='match'),
            models.B(id_override='25', int_column=5, another_string='NO MATCH!!!!')
        ]
        for row in rows:
            session.add(row)
        session.commit()
        session.close()

        db = DefaultDatabase(session_factory, models_list)

        def __make_db_and_filter(and_: AndFilter) -> DatabaseFilter:
            return DefaultDatabaseFilter(
                DataSourceFilter(and_=and_)
            )

        def __assert_count(and_: AndFilter, expected_count: int) -> None:
            db_filter = __make_db_and_filter(and_)
            count = db.count('b', sess, filters=db_filter)

            assert count == expected_count

        # eq
        __assert_count(
            {
                'another_string': {
                    'eq': {
                        'value': 'match'
                    }
                }
            },
            3
        )

        # not-eq
        __assert_count(
            {
                'another_string': {
                    'eq': {
                        'value': 'match',
                        'negate': True
                    }
                }
            },
            2
        )

        # contains
        __assert_count(
            {
                'another_string': {
                    'contains': {
                        'value': 'atc'
                    }
                }
            },
            4
        )

        # not contains
        __assert_count(
            {
                'another_string': {
                    'contains': {
                        'value': 'atc',
                        'negate': True
                    }
                }
            },
            1
        )

        # in list (`id` _not_ `id_override`)
        __assert_count(
            {
                'id': {
                    'in_list': {
                        'value': [
                            '1',
                            '3'
                        ]
                    }
                }
            },
            1
        )

        # not in list (`id` _not_ `id_override`)
        __assert_count(
            {
                'id': {
                    'in_list': {
                        'value': [
                            '1',
                            '3'
                        ],
                        'negate': True
                    }
                }
            },
            4
        )

        # less than
        __assert_count(
            {
                'int_column': {
                    'lt': {
                        'value': 2
                    }
                }
            },
            1
        )

        # greater than
        __assert_count(
            {
                'int_column': {
                    'gt': {
                        'value': 2
                    }
                }
            },
            3
        )

        # less than or equal to
        __assert_count(
            {
                'int_column': {
                    'lte': {
                        'value': 2
                    }
                }
            },
            2
        )

        # greater than or equal to
        __assert_count(
            {
                'int_column': {
                    'gte': {
                        'value': 2
                    }
                }
            },
            4
        )

        # a complex mixture
        __assert_count(
            {
                'int_column': {
                    'gte': {
                        'value': 2
                    },
                    'lt': {
                        'value': 4
                    }
                },
                'another_string': {
                    'exists': {
                        'negate': True
                    }
                }
            },
            1
        )
