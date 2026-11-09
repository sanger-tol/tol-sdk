# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
from typing import Any

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
        # Upsert data objects with different combinations of null and non-null columns
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

    @against(elastic, api_elastic)
    def test_math_function(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        # Upsert data objects
        data_objects = [
            data_source.data_object_factory(
                'root',
                str(id_),
                attributes={
                    'int_column': 144,
                    'double_column': float(id_),
                    'bool_column': True if id_ % 2 == 0 else False
                },
            )
            for id_ in range(10)
        ]
        data_source.upsert('root', data_objects, provenance='source1')
        ds_sleep(2)

        # Get by ID
        first = list(data_source.get_by_ids('root', ['0', '2', '6']))
        assert len(first) == 3

        # The first one is a division by zero
        # TODO Return this as a value to display error in the UI.
        # We can't use pytest.raises for the division by zero here because the error happens
        # within the runtime field in Elastic
        ret = first[0]
        assert ret is not None
        # ...

        # The second one should divide 144 by 2
        ret = first[1]
        assert ret is not None
        assert ret.math_runtime_field == 72
        assert ret.attributes['math_runtime_field'] == 72

        # The third one should divide 144 by 6
        ret = first[2]
        assert ret is not None
        assert ret.math_runtime_field == 24
        assert ret.attributes['math_runtime_field'] == 24

        # Get list by runtime field query.
        # 28.8 is 144/5, so it should include exactly half of the data objects
        # (as `gt` is non-inclusive)
        f = DataSourceFilter()
        f.and_ = {
            'math_runtime_field': {'gt': {'value': 28.8}},
            # Exclude archetypes
            'id': {
                'exists': {},
                'contains': {'value': '#', 'negate': True}
            },
        }
        second = list(data_source.get_list('root', object_filters=f))
        print([obj.id for obj in second])
        assert len(second) == 5

        # Do the same but with get_list_page
        # (but this time we check for the other half)
        f = DataSourceFilter()
        f.and_ = {
            'math_runtime_field': {'lt': {'value': 36}},
            # Exclude archetypes
            'id': {
                'exists': {},
                'contains': {'value': '#', 'negate': True}
            },
        }
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
        # assert fourth[0].math_runtime_field == 'first_0'   # id 0
        assert fourth[1].math_runtime_field == 72  # id 2
        assert fourth[2].math_runtime_field == 36  # id 4
        assert fourth[3].math_runtime_field == 24  # id 6
        assert fourth[4].math_runtime_field == 18  # id 8

    @against(elastic, api_elastic)
    def test_min_function(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        # Upsert data objects
        data_objects = [
            data_source.data_object_factory(
                'root',
                str(id_),
                attributes={
                    'int_column': 5,
                    'double_column': float(id_),
                    'bool_column': True if id_ % 2 == 0 else False
                },
            )
            for id_ in range(10)
        ]
        data_source.upsert('root', data_objects, provenance='source1')
        ds_sleep(2)

        # Get by ID
        first = list(data_source.get_by_ids('root', ['1', '5', '8']))
        assert len(first) == 3

        # For the first one, the ID is less than 5 so should take precedence
        ret = first[0]
        assert ret is not None
        assert ret.min_runtime_field == 1
        assert ret.attributes['min_runtime_field'] == 1

        # For the second one, they're the same value
        ret = first[1]
        assert ret is not None
        assert ret.min_runtime_field == 5
        assert ret.attributes['min_runtime_field'] == 5

        # For the third one, the ID is greater than 5
        ret = first[2]
        assert ret is not None
        assert ret.min_runtime_field == 5
        assert ret.attributes['min_runtime_field'] == 5

        # Get list by runtime field query.
        # Half of them should be less than 5 (as they're the min)
        f = DataSourceFilter()
        f.and_ = {
            'min_runtime_field': {'lt': {'value': 5}},
            # Exclude archetypes
            'id': {
                'exists': {},
                'contains': {'value': '#', 'negate': True}
            },
        }
        second = list(data_source.get_list('root', object_filters=f))
        print([obj.id for obj in second])
        assert len(second) == 5

        # Do the same but with get_list_page
        # (but this time we check for the other half, so they should all be 5)
        f = DataSourceFilter()
        f.and_ = {
            'min_runtime_field': {'eq': {'value': 5}},
            # Exclude archetypes
            'id': {
                'exists': {},
                'contains': {'value': '#', 'negate': True}
            },
        }
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
        assert fourth[0].min_runtime_field == 0  # id 0
        assert fourth[1].min_runtime_field == 2  # id 2
        assert fourth[2].min_runtime_field == 4  # id 4
        assert fourth[3].min_runtime_field == 5  # id 6
        assert fourth[4].min_runtime_field == 5  # id 8
