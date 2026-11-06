# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable

from tol.core import DataSourceFilter, OperableDataSource

from ..dec import against
from ..fixtures import api_elastic, elastic


class TestRuntimeFields:
    @against(elastic, api_elastic)
    def test_script_field(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        """
        Test a script runtime field.
        
        Tests against the `script_runtime_field` column in the archetype, which is a boolean that's
        the opposite of whatever `bool_column` holds.
        This test upserts data objects, then checks that the runtime field functions correctly
        when fetching data.
        """
        # Upsert some data objects to the elastic index.
        # They each have a value for `bool_column`, which is a dependency of the
        # `script_runtime_field` runtime field that will be queried
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
        assert ret.script_runtime_field is True
        assert ret.attributes['script_runtime_field'] is True
        ret = first[1]
        assert ret is not None
        assert ret.script_runtime_field is False
        assert ret.attributes['script_runtime_field'] is False

        # Get list by runtime field query
        f = DataSourceFilter()
        f.and_ = {'script_runtime_field': {'eq': {'value': True}}}
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
        assert fourth[0].script_runtime_field is False
        assert fourth[1].script_runtime_field is False
        assert fourth[2].script_runtime_field is False
        assert fourth[3].script_runtime_field is False
        assert fourth[4].script_runtime_field is False
        assert fourth[5].script_runtime_field is False
