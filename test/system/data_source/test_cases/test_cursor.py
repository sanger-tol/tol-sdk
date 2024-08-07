# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter, OperableDataSource

from ..dec import against
from ..fixtures import all_fixtures, api_sql, sql


class TestListGetCursor:
    """
    Tests `.get_list()` with `.get_cursor_page`
    for real `DataSource` instances.

    N.B. - all 3 `DataSource` classes under
    test use cursor paging for list getting.

    (`ApiDataSource` prefers cursor pagination,
    but falls back to limit-offset where
    necessary).
    """

    @against(*all_fixtures)
    def test_get_cursor_page(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):
        """
        Empty then populated cursor page, with
        standard fizzbuzz filtering.
        """

        # empty list
        with data_source.get_session() as sess:
            f = DataSourceFilter(
                and_={
                    'int_column': {
                        'eq': {
                            'value': 42,
                            'negate': True
                        }
                    }
                }
            )
            return_value = sess.get_cursor_page(
                'root',
                page_size=4,
                object_filters=f
            )
            expected = [], None
            observed = list(return_value[0]), return_value[1]

            assert expected == observed

        # populate the data
        objs = (
            data_source.data_object_factory(
                'root',
                id_='a' * i,
                attributes={
                    'str_column': self.__get_fizzbuzz(i)
                }
            )
            for i in range(1, 51)
        )
        data_source.upsert('root', objs)
        ds_sleep(7)

        # start from beginning (no `search_after`) on "fizz"
        fetched, search_after = data_source.get_cursor_page(
            'root',
            page_size=3,
            object_filters=DataSourceFilter(
                and_={
                    'int_column': {
                        'eq': {
                            'value': 42,
                            'negate': True
                        }
                    },
                    'str_column': {
                        'contains': {
                            'value': 'fizz'
                        }
                    }
                }
            )
        )
        assert search_after == ['a' * 6]
        observed = list(fetched)
        assert len(observed) == 3
        for i, obj in enumerate(observed, start=1):
            length = i * 2
            assert obj.id == 'a' * length
            assert 'fizz' in obj.str_column

        # start from a later `search_after` on "buzz"
        fetched, search_after = data_source.get_cursor_page(
            'root',
            page_size=3,
            object_filters=DataSourceFilter(
                and_={
                    'int_column': {
                        'eq': {
                            'value': 42,
                            'negate': True
                        }
                    },
                    'str_column': {
                        'contains': {
                            'value': 'buzz'
                        }
                    }
                }
            ),
            search_after=['a' * 15]
        )
        assert search_after == ['a' * 30]
        observed = list(fetched)
        assert len(observed) == 3
        for i, obj in enumerate(observed, start=4):
            length = i * 5
            assert obj.id == 'a' * length
            assert 'buzz' in obj.str_column

    @against(*all_fixtures)
    def test_get_list(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):
        """
        Empty then populated `get_list()`, with
        standard is_even filtering.

        Note that sorting cannot be specified on
        `get_list()`.
        """

        # override `page_size`
        data_source.page_size = 3

        # empty list
        with data_source.get_session() as sess:
            f = DataSourceFilter(
                and_={
                    'int_column': {
                        'eq': {
                            'value': 42,
                            'negate': True
                        }
                    }
                }
            )
            return_value = sess.get_list(
                'root',
                object_filters=f
            )
            expected = []
            fetched = list(return_value)

            assert expected == fetched

        # populate the data
        ids = [
            str(i)
            for i in range(25)
        ]
        objs = (
            data_source.data_object_factory(
                'root',
                id_,
                attributes={
                    'bool_column': int(id_) % 2 == 0
                }
            )
            for id_ in ids
        )
        data_source.upsert(
            'root',
            objs
        )
        ds_sleep(7)

        # evens
        fetched = list(
            data_source.get_list(
                'root',
                DataSourceFilter(
                    and_={
                        'int_column': {
                            'eq': {
                                'value': 42,
                                'negate': True
                            }
                        },
                        'bool_column': {
                            'eq': {
                                'value': True
                            }
                        }
                    }
                )
            )
        )
        assert len(fetched) == 13
        expected = {str(i) for i in range(0, 25, 2)}
        observed = {o.id for o in fetched}
        assert observed == expected

        # odds
        fetched = list(
            data_source.get_list(
                'root',
                DataSourceFilter(
                    and_={
                        'int_column': {
                            'eq': {
                                'value': 42,
                                'negate': True
                            }
                        },
                        'bool_column': {
                            'eq': {
                                'value': False
                            }
                        }
                    }
                )
            )
        )
        assert len(fetched) == 12
        expected = {str(i) for i in range(1, 25, 2)}
        observed = {o.id for o in fetched}
        assert observed == expected

    @against(sql, api_sql)  # elastic is funky with the archetypes
    def test_get_list_without_filter(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):
        """
        `.get_list()` with cursor paging and
        no specified filters.
        """

        data_source.page_size = 2

        objs = (
            data_source.data_object_factory(
                'related',
                str(i)
            )
            for i in range(13)
        )

        data_source.upsert('related', objs)

        fetched = list(
            data_source.get_list('related')
        )

        # 13 inserted + 1 archetype
        assert len(fetched) == 14

    def __get_fizzbuzz(self, in_: int) -> str:
        """
        Wrong order, due to a limitation on
        `contains` filters in `ElasticDataSource`,
        so technically buzz-fizz
        """

        out_ = ''
        if in_ % 5 == 0:
            out_ += 'buzz'
        if in_ % 2 == 0:
            out_ += 'fizz'
        return out_
