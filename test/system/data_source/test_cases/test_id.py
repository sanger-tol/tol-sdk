# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter, OperableDataSource
from tol.core.operator import RelationWriteMode

from ..dec import against
from ..fixtures import all_fixtures


class TestID:
    """
    Filtering and Sorting against ID's
    and relation ID's

    (regression TOLP-7740)
    """

    @against(*all_fixtures)
    def test_sort(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):

        objs = (
            data_source.data_object_factory(
                'root',
                f'id_{i}',
                attributes={
                    'str_column': 'AA' * i,
                    'int_column': 424242
                }
            )
            for i in range(3)
        )

        data_source.upsert('root', objs)

        # let upsert settle
        ds_sleep(5)

        # filter out archetypes
        filters = DataSourceFilter(
            and_={
                'int_column': {
                    'eq': {
                        'value': 424242
                    }
                }
            }
        )

        ascending_objs, _ = data_source.get_list_page(
            'root',
            1,
            page_size=10,
            sort_by='id',
            object_filters=filters
        )
        for i, obj in enumerate(ascending_objs):
            assert obj.id == f'id_{i}'
            assert obj.str_column == 'AA' * i

        descending_objs, _ = data_source.get_list_page(
            'root',
            1,
            page_size=10,
            sort_by='-id',
            object_filters=filters
        )
        for i, obj in enumerate(descending_objs):
            inverted = 2 - i
            assert obj.id == f'id_{inverted}'
            assert obj.str_column == 'AA' * inverted

    @against(*all_fixtures)
    def test_filter(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):

        objs = (
            data_source.data_object_factory(
                'root',
                f'id_{"B" * i}',
                attributes={
                    'int_column': 424242
                }
            )
            for i in range(3)
        )

        data_source.upsert('root', objs)

        # let upsert settle
        ds_sleep(5)

        in_list = list(
            data_source.get_list(
                'root',
                object_filters=DataSourceFilter(
                    and_={
                        'int_column': {
                            'eq': {
                                'value': 424242
                            }
                        },
                        'id': {
                            'in_list': {
                                'value': [
                                    'id_',
                                    'id_BB'
                                ]
                            }
                        }
                    }
                )
            )
        )
        assert len(in_list) == 2

        eq = list(
            data_source.get_list(
                'root',
                object_filters=DataSourceFilter(
                    and_={
                        'int_column': {
                            'eq': {
                                'value': 424242
                            }
                        },
                        'id': {
                            'eq': {
                                'value': 'id_B'
                            }
                        }
                    }
                )
            )
        )
        assert len(eq) == 1

    @against(*all_fixtures)
    def test_sort_relation(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):

        relations = [
            data_source.data_object_factory(
                'related',
                f'relation_{i}',
            )
            for i in range(3)
        ]

        roots = [
            data_source.data_object_factory(
                'root',
                str(i),
                attributes={
                    'int_column': 424242
                },
                to_one={
                    'related_object': related
                }
            )
            for i, related in enumerate(relations)
        ]

        if data_source.write_mode['root'] == RelationWriteMode.SEPARATE:
            data_source.upsert('related', relations)
        data_source.upsert('root', roots)

        # let upsert settle
        ds_sleep(5)

        # filter out archetypes
        filters = DataSourceFilter(
            and_={
                'int_column': {
                    'eq': {
                        'value': 424242
                    }
                }
            }
        )

        ascending_objs, _ = data_source.get_list_page(
            'root',
            1,
            page_size=10,
            sort_by='related_object.id',
            object_filters=filters
        )
        for i, obj in enumerate(ascending_objs):
            assert obj.id == str(i)
            assert obj.related_object.id == f'relation_{i}'

        descending_objs, _ = data_source.get_list_page(
            'root',
            1,
            page_size=10,
            sort_by='-related_object.id',
            object_filters=filters
        )
        for i, obj in enumerate(descending_objs):
            inverted = 2 - i
            assert obj.id == str(inverted)
            assert obj.related_object.id == f'relation_{inverted}'

    @against(*all_fixtures)
    def test_filter_relation(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):

        relations = [
            data_source.data_object_factory(
                'related',
                f'relation_{i}',
            )
            for i in range(3)
        ]

        roots = [
            data_source.data_object_factory(
                'root',
                str(i),
                attributes={
                    'int_column': 424242
                },
                to_one={
                    'related_object': related
                }
            )
            for i, related in enumerate(relations)
        ]

        if data_source.write_mode['root'] == RelationWriteMode.SEPARATE:
            data_source.upsert('related', relations)
        data_source.upsert('root', roots)

        # let upsert settle
        ds_sleep(5)

        in_list = list(
            data_source.get_list(
                'root',
                object_filters=DataSourceFilter(
                    and_={
                        'int_column': {
                            'eq': {
                                'value': 424242
                            }
                        },
                        'related_object.id': {
                            'in_list': {
                                'value': [
                                    'relation_0',
                                    'relation_2'
                                ]
                            }
                        }
                    }
                )
            )
        )
        assert len(in_list) == 2

        eq = list(
            data_source.get_list(
                'root',
                object_filters=DataSourceFilter(
                    and_={
                        'int_column': {
                            'eq': {
                                'value': 424242
                            }
                        },
                        'related_object.id': {
                            'eq': {
                                'value': 'relation_1'
                            }
                        }
                    }
                )
            )
        )
        assert len(eq) == 1
