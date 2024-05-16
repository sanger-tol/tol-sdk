# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock, create_autospec

from pytest import fixture

from tol.core import DataSourceFilter
from tol.core.datasource_filter import AndFilter
from tol.core.relationship import RelationshipConfig
from tol.sql.database import DefaultDatabase
from tol.sql.filter import DatabaseFilter, DefaultDatabaseFilter
from tol.sql.relationship import SqlRelationshipConfig

from .. import models


@fixture(scope='module')
def type_tablename_dict(models_list) -> dict[str, str]:
    return {
        m.__tablename__: m.__tablename__ for m in models_list
    }


class TestDefaultDatabaseFilter:

    def test_exact_filter(self, session_factory, models_list, type_tablename_dict):
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
            DataSourceFilter(exact={'string_column': 'even'}),
            type_tablename_dict,
            Mock()
        )
        count = db.count('a', filters=even_filter)
        assert count == 4
        evens = db.get_page('a', filters=even_filter)
        for i, even in enumerate(evens):
            assert even.instance_id == str(i * 2)
            assert even.instance_attributes == {'string_column': 'even'}

        # check the odds [1, 3, 5]
        odd_filter = DefaultDatabaseFilter(
            DataSourceFilter(exact={'string_column': 'odd'}),
            type_tablename_dict,
            Mock()
        )
        count = db.count('a', filters=odd_filter)
        assert count == 3
        odds = db.get_page('a', filters=odd_filter)
        for i, odd in enumerate(odds):
            assert odd.instance_id == str(i * 2 + 1)
            assert odd.instance_attributes == {'string_column': 'odd'}

    def test_all_filters(self, session_factory, models_list, type_tablename_dict):
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
        db_filter = DefaultDatabaseFilter(ds_filter, type_tablename_dict, Mock())

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

    def test_and_(self, session_factory, models_list, type_tablename_dict):
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
                DataSourceFilter(and_=and_),
                type_tablename_dict,
                create_autospec(SqlRelationshipConfig, spec_set=True)
            )

        def __assert_count(and_: AndFilter, expected_count: int) -> None:
            db_filter = __make_db_and_filter(and_)
            count = db.count('b', filters=db_filter)

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

    def test_relation(self, session_factory, models_list, type_tablename_dict):
        """
        `DefaultDatabaseFilter().filter()` using an `exact` term
        with relationships.
        """

        session = session_factory()
        rows = [
            models.R1(
                id_override='101',
                r2_foreign_key='102',
                r5_foreign_key='105',
            ),
            models.R2(id='102'),
            models.R4(id_r4='104'),
            models.R5(id='105', funny_word='happy'),
            # two `R3`'s pointing to the `R2` via our `R1`
            models.R3(id='1030', ur_r1_id='101'),
            # one of which also points at our `R4`
            models.R3(id='1031', ur_r1_id='101', r4_foreign_key='104'),
            # one `R3` pointing nowhere
            models.R3(id='103404'),
        ]
        for row in rows:
            session.add(row)
        session.commit()

        db = DefaultDatabase(session_factory, models_list)

        mock_relationship_config = create_autospec(
            SqlRelationshipConfig,
            spec_set=True
        )
        mock_relationship_config.to_dict.return_value = {
            'r1': RelationshipConfig(
                to_one={
                    'r2_d2': 'r2',
                    'this_lovely_r5': 'r5'
                }
            ),
            'r3': RelationshipConfig(
                to_one={
                    'funny_r1': 'r1',
                    'r4_mine': 'r4'
                }
            ),
        }

        ds_filter = DataSourceFilter(
            exact={
                'funny_r1.r2_d2.id': '102',  # 2 meet this condition
                # only 1 of these 2 also matches the following
                'r4_mine.id': '104',
                # this is just to test for an attribute other than `id`
                'funny_r1.this_lovely_r5.funny_word': 'happy',
            }
        )
        db_filter = DefaultDatabaseFilter(
            ds_filter,
            type_tablename_dict,
            mock_relationship_config
        )

        # there can be only one
        count = db.count('r3', filters=db_filter)
        assert count == 1

        # check it's the right one
        (r3_instance,) = list(
            db.get_page('r3', filters=db_filter)
        )
        assert r3_instance.instance_id == '1031'
