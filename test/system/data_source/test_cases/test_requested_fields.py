
# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import (
    DataObject,
    DataSourceFilter,
    OperableDataSource
)

from ..dec import against
from ..fixtures import api_sql, sql


class TestRequestedFields:
    """
    Specifying `requested_fields` on various GET methods
    cuts down on lazy fetches.
    """

    @against(api_sql, sql)
    def test_get_cursor_page(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):

        self.__insert_mock_data(data_source)

        (iter_root, _) = data_source.get_cursor_page(
            'root',
            requested_fields=['related_object.str_column'],
            object_filters=self.__eq_ob_filter(),
        )
        (root,) = list(iter_root)

        self.__do_asserts(root)

    @against(api_sql, sql)
    def test_get_by_ids(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):

        self.__insert_mock_data(data_source)

        iter_root = data_source.get_by_ids(
            'root',
            ['idc'],
            requested_fields=['related_object.str_column'],
        )
        (root,) = list(iter_root)

        self.__do_asserts(root)

    @against(api_sql, sql)
    def test_get_list_page(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):

        self.__insert_mock_data(data_source)

        (iter_root, _) = data_source.get_list_page(
            'root',
            1,
            requested_fields=['related_object.str_column'],
            object_filters=self.__eq_ob_filter(),
        )
        (root,) = list(iter_root)

        self.__do_asserts(root)

    @against(api_sql, sql)
    def test_get_list(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ):

        self.__insert_mock_data(data_source)

        iter_root = data_source.get_list(
            'root',
            requested_fields=['related_object.str_column'],
            object_filters=self.__eq_ob_filter(),
        )
        (root,) = list(iter_root)

        self.__do_asserts(root)

    def __insert_mock_data(
        self,
        data_source: OperableDataSource,
    ) -> None:

        rel = data_source.data_object_factory(
            'related',
            'anything',
            {
                'str_column': 'hype'
            }
        )
        data_source.upsert('related', [rel])

        root = data_source.data_object_factory(
            'root',
            'idc',
            to_one={
                'related_object': rel
            }
        )
        data_source.upsert('root', [root])

    def __eq_ob_filter(self) -> DataSourceFilter:
        return DataSourceFilter(
            and_={
                'id': {
                    'eq': {
                        'value': 'idc'
                    }
                }
            }
        )

    def __do_asserts(
        self,
        root: DataObject,
    ) -> None:

        assert 'related_object' in root._to_one_objects

        assert root.related_object.str_column == 'hype'
