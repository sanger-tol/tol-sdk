# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter, OperableDataSource
from tol.core.operator import RelationWriteMode

from ..dec import against
from ..fixtures import all_fixtures


class TestDataSourceSession:
    """
    Tests `.get_session()` for real `DataSource`
    instances.
    """

    @against(*all_fixtures)
    def test_get_session_single(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):
        """
        A mixture of operations work as expected in
        a single session.
        """

        with data_source.get_session() as sess:
            rel = sess.data_object_factory(
                'related',
                '900',
                attributes={
                    'str_column': 'lol'
                }
            )
            root = sess.data_object_factory(
                'root',
                '100',
                to_one={
                    'related_object': rel
                }
            )

            if data_source.write_mode['root'] == RelationWriteMode.SEPARATE:
                sess.upsert('related', [rel], provenance='source1')
            sess.upsert('root', [root], provenance='source1')

            ds_sleep(2)

            by_id = sess.get_one('root', '100')
            assert by_id is not None

            f = DataSourceFilter(
                and_={
                    'related_object.id': {
                        'eq': {
                            'value': '900'
                        }
                    },
                    'related_object.str_column': {
                        'eq': {
                            'value': 'ABSOLUTELY WRONG!',
                            'negate': True
                        }
                    }
                }
            )
            by_list = list(
                sess.get_list(
                    'root',
                    object_filters=f
                )
            )
            assert len(by_list) == 1

    @against(*all_fixtures)
    def test_get_session_multiple(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):
        """
        Multiple sessions don't break
        """

        with data_source.get_session() as sess1:
            rel = sess1.data_object_factory(
                'related',
                '900',
                attributes={
                    'str_column': 'lol'
                }
            )
            root = sess1.data_object_factory(
                'root',
                '100',
                to_one={
                    'related_object': rel
                }
            )

            if data_source.write_mode['root'] == RelationWriteMode.SEPARATE:
                sess1.upsert('related', [rel], provenance='source1')
            sess1.upsert('root', [root], provenance='source1')

        ds_sleep(2)

        with data_source.get_session() as sess2:
            by_id = sess2.get_one('root', '100')
            assert by_id is not None

            f = DataSourceFilter(
                and_={
                    'related_object.id': {
                        'eq': {
                            'value': '900'
                        }
                    },
                    'related_object.str_column': {
                        'eq': {
                            'value': 'ABSOLUTELY WRONG!',
                            'negate': True
                        }
                    }
                }
            )

        with data_source.get_session() as sess3:
            by_list = list(
                sess3.get_list(
                    'root',
                    object_filters=f
                )
            )
            assert len(by_list) == 1
