# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import DataSourceFilter, OperableDataSource

from ..dec import against
from ..fixtures import api_elastic, elastic


class TestRuntimeFields:
    @against(elastic, api_elastic)
    def test_script_fields(self, data_source: OperableDataSource, ds_sleep):
        """
        Upsert a `DataObject` instance, and then query a runtime field
        """
        data_objects = [
            data_source.data_object_factory(
                'root',
                str(id_),
                attributes={
                    'str_column': f'test_{id_}',
                    'bool_column': True if id_ % 2 == 0 else False,
                },
            )
            for id_ in range(10)
        ]
        data_source.upsert('root', data_objects, provenance='source1')
        ds_sleep(2)

        # Get by ID
        first = list(data_source.get_by_ids('root', ['1', '2']))
        assert len(first) == 2
        ret = first[0]
        assert ret is not None
        assert ret.runtime_column is True
        assert ret.attributes['runtime_column'] is True
        ret = first[1]
        assert ret is not None
        assert ret.runtime_column is False
        assert ret.attributes['runtime_column'] is False

        # Get list by runtime field query
        f = DataSourceFilter()
        f.and_ = {'runtime_column': {'eq': {'value': True}}}
        second = list(data_source.get_list('root', object_filters=f))
        assert len(second) == 5

        # Get list page by runtime field query
        third, _ = data_source.get_list_page('root', 1, object_filters=f, page_size=20)
        assert len(list(third)) == 5

        # Get list and check runtime field
        f = DataSourceFilter()
        f.and_ = {'bool_column': {'eq': {'value': True}}}
        fourth = list(data_source.get_list('root', object_filters=f))
        assert len(fourth) == 6  # 5 plus archetype
        assert fourth[0].runtime_column is False
        assert fourth[1].runtime_column is False
        assert fourth[2].runtime_column is False
        assert fourth[3].runtime_column is False
        assert fourth[4].runtime_column is False
        assert fourth[5].runtime_column is False
