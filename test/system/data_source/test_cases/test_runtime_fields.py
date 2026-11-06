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

        # Perform a get_list filtered on a different field, then check the runtime field
        f = DataSourceFilter()
        f.and_ = {
            'bool_column': {'eq': {'value': True}},
            # Exclude archetypes
            'id': {
                'exists': {},
                'contains': {'value': '#', 'negate': True}
            },
        }
        fourth = list(data_source.get_list('root', object_filters=f))
        assert len(fourth) == 5
        assert fourth[0].script_runtime_field is False
        assert fourth[1].script_runtime_field is False
        assert fourth[2].script_runtime_field is False
        assert fourth[3].script_runtime_field is False
        assert fourth[4].script_runtime_field is False

    @against(elastic, api_elastic)
    def test_if_function(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        # Upsert data objects where half have the condition fulfilled and half do not
        data_objects = [
            data_source.data_object_factory(
                'root',
                str(id_),
                attributes={
                    'bool_column': True if id_ % 2 == 0 else False,
                    'str_column': f'first_{id_}',
                    'str_column_2': f'second_{id_}'
                },
            )
            for id_ in range(10)
        ]
        data_source.upsert('root', data_objects, provenance='source1')
        ds_sleep(2)

        # Get by ID
        first = list(data_source.get_by_ids('root', ['1', '2']))
        assert len(first) == 2

        # The first one should have its condition fail (`bool_column` is False)
        # so it have the value in `str_column_2`
        ret = first[0]
        assert ret is not None
        assert ret.if_runtime_field == 'second_1'
        assert ret.attributes['if_runtime_field'] == 'second_1'

        # The second one should have its condition pass (`bool_column` is True)
        # so it have the value in `str_column`
        ret = first[1]
        assert ret is not None
        assert ret.if_runtime_field == 'first_2'
        assert ret.attributes['if_runtime_field'] == 'first_2'

        # Get list by runtime field query.
        # Half of them should have the condition pass
        f = DataSourceFilter()
        f.and_ = {'if_runtime_field': {'contains': {'value': 'first'}}}
        second = list(data_source.get_list('root', object_filters=f))
        assert len(second) == 5

        # Do the same but with get_list_page.
        # Half of them should have the condition fail
        f = DataSourceFilter()
        f.and_ = {'if_runtime_field': {'contains': {'value': 'second'}}}
        third, _ = data_source.get_list_page('root', 1, object_filters=f, page_size=20)
        assert len(list(third)) == 5

        # Perform a get_list filtered on a different field, then check the runtime field
        f = DataSourceFilter()
        f.and_ = {
            'bool_column': {'eq': {'value': True}},
            # Exclude archetypes
            'id': {
                'exists': {},
                'contains': {'value': '#', 'negate': True}
            },
        }
        fourth = list(data_source.get_list('root', object_filters=f))
        assert len(fourth) == 5
        for obj in fourth:
            assert type(obj.if_runtime_field) == str
            assert 'first' in obj.if_runtime_field

    @against(elastic, api_elastic)
    def test_coalesce_function(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        # Upsert data objects where half have the condition fulfilled and half do not
        data_objects = [
            data_source.data_object_factory(
                'root',
                str(id_),
                attributes={
                    'str_column': f'first_{id_}' if id_ % 3 == 0 else None,
                    'str_column_2': f'second_{id_}' if id_ % 2 == 0 else None,
                    'bool_column': True if id_ % 2 == 0 else False
                },
            )
            for id_ in range(10)
        ]
        data_source.upsert('root', data_objects, provenance='source1')
        ds_sleep(2)

        # Get by ID
        first = list(data_source.get_by_ids('root', ['1', '2', '6']))
        assert len(first) == 3

        # The first one should resolve to None
        # because 1 is neither divisible by 2 nor 3
        ret = first[0]
        assert ret is not None
        assert ret.coalesce_runtime_field is None
        assert 'coalesce_runtime_field' not in ret.attributes

        # The second one should resolve to the value of `str_column_2`
        # because 2 is divisible by 2 but not by 3
        ret = first[1]
        assert ret is not None
        assert ret.coalesce_runtime_field == 'second_2'
        assert ret.attributes['coalesce_runtime_field'] == 'second_2'

        # The third one should resolve to the value of `str_column`
        # because 6 is divisible by both 2 and 3, but `str_column` is the first in the field list
        ret = first[2]
        assert ret is not None
        assert ret.coalesce_runtime_field == 'first_6'
        assert ret.attributes['coalesce_runtime_field'] == 'first_6'

        # Get list by runtime field query.
        # As we're filtering the *coalesced* result, the only IDs that should resolve to the
        # second field are 2, 4, and 8.
        f = DataSourceFilter()
        f.and_ = {'coalesce_runtime_field': {'contains': {'value': 'second'}}}
        second = list(data_source.get_list('root', object_filters=f))
        print([obj.id for obj in second])
        assert len(second) == 3

        # Do the same but with get_list_page
        f = DataSourceFilter()
        f.and_ = {'coalesce_runtime_field': {'contains': {'value': 'second'}}}
        third, _ = data_source.get_list_page('root', 1, object_filters=f, page_size=20)
        assert len(list(third)) == 3

        # Perform a get_list filtered on a different field, then check the runtime field
        f = DataSourceFilter()
        f.and_ = {
            'bool_column': {'eq': {'value': True}},
            # Exclude archetypes
            'id': {
                'exists': {},
                'contains': {'value': '#', 'negate': True}
            },
        }
        fourth = list(data_source.get_list('root', object_filters=f))
        assert len(fourth) == 5
        assert fourth[0].coalesce_runtime_field == 'first_0'   # id 0
        assert fourth[1].coalesce_runtime_field == 'second_2'  # id 2
        assert fourth[2].coalesce_runtime_field == 'second_4'  # id 4
        assert fourth[3].coalesce_runtime_field == 'first_6'   # id 6
        assert fourth[4].coalesce_runtime_field == 'second_8'  # id 8
