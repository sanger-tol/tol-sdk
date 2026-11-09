# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from tol.core import DataObject, DataSourceFilter, OperableDataSource
from tol.core.datasource_filter import AndFilter

from ..dec import against
from ..fixtures import api_elastic, elastic


class TestRuntimeFields:
    def upsert_data_objects(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None],
        *,
        attributes: Callable[[int], dict[str, Any]]
    ) -> None:
        """
        To be called to set up each test.

        Upserts 10 data objects into the Elastic index, where the bool_column alternates
        between True and False, and they also have the attributes provided (based on their ID).
        """
        data_objects = [
            data_source.data_object_factory(
                'root',
                str(id_),
                attributes={
                    'bool_column': True if id_ % 2 == 0 else False,
                    **attributes(id_)
                },
            )
            for id_ in range(10)
        ]
        data_source.upsert('root', data_objects, provenance='source1')
        ds_sleep(2)

    def assert_correct_runtime_field_values(
        self,
        data_objects: list[DataObject | None] | list[DataObject],
        attribute_name: str,
        expected_values: list[Any]
    ) -> None:
        """
        Utility function to check the value of the runtime field attribute for multiple
        data objects
        """
        assert len(data_objects) == len(expected_values)
        for obj, expected_value in zip(data_objects, expected_values):
            assert obj is not None
            if expected_value is None:
                # We can't index into obj.attributes if the expected value is None,
                # so handle this is a separate case
                assert getattr(obj, attribute_name) is None
                assert attribute_name not in obj.attributes
            else:
                assert getattr(obj, attribute_name) == expected_value
                assert obj.attributes[attribute_name] == expected_value

    def get_list_filtered(
        self,
        data_source: OperableDataSource,
        filter_: AndFilter,
        *,
        paged: bool = False
    ) -> list[DataObject]:
        f = DataSourceFilter()
        f.and_ = {
            **filter_,
            # Exclude archetypes
            'id': {
                'exists': {},
                'contains': {'value': '#', 'negate': True}
            }
        }

        if paged:
            return list(data_source.get_list_page('root', 1, object_filters=f, page_size=20)[0])
        else:
            return list(data_source.get_list('root', object_filters=f))

    def get_every_other_data_object(self, data_source: OperableDataSource) -> list[DataObject]:
        """
        The upserted data objects have bool_column be True on records with even IDs.
        This returns only those records.
        """
        return self.get_list_filtered(data_source, {'bool_column': {'eq': {'value': True}}})

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
        self.upsert_data_objects(
            data_source,
            ds_sleep,
            attributes=lambda id_: {
                'str_column': f'test_{id_}'
            }
        )

        # Get by ID
        first = list(data_source.get_by_ids('root', ['1', '2']))
        self.assert_correct_runtime_field_values(
            first,
            'script_runtime_field',
            [True, False]
        )

        # Get list by runtime field query
        second = self.get_list_filtered(
            data_source,
            {'script_runtime_field': {'eq': {'value': True}}},
        )
        assert len(second) == 5

        # Get list page by runtime field query
        third = self.get_list_filtered(
            data_source,
            {'script_runtime_field': {'eq': {'value': True}}},
            paged=True
        )
        assert len(third) == 5

        # Perform a get_list filtered on a different field, then check the runtime field
        fourth = self.get_every_other_data_object(data_source)
        self.assert_correct_runtime_field_values(
            fourth,
            'script_runtime_field',
            [False, False, False, False, False]
        )

    @against(elastic, api_elastic)
    def test_if_function(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        # Upsert data objects where half have the condition fulfilled and half do not
        self.upsert_data_objects(
            data_source,
            ds_sleep,
            attributes=lambda id_: {
                'str_column': f'first_{id_}',
                'str_column_2': f'second_{id_}'
            }
        )

        # Get by ID
        first = list(data_source.get_by_ids('root', ['1', '2']))
        self.assert_correct_runtime_field_values(
            first,
            'if_runtime_field',
            [
                # The first one should have its condition fail (`bool_column` is False)
                # so it have the value in `str_column_2`
                'second_1',
                # The second one should have its condition pass (`bool_column` is True)
                # so it have the value in `str_column`
                'first_2'
            ]
        )

        # Get list by runtime field query.
        # Half of them should have the condition pass
        second = self.get_list_filtered(
            data_source,
            {'if_runtime_field': {'contains': {'value': 'first'}}},
        )
        assert len(second) == 5

        # Do the same but with get_list_page.
        # Half of them should have the condition fail
        third = self.get_list_filtered(
            data_source,
            {'if_runtime_field': {'contains': {'value': 'second'}}},
            paged=True
        )
        assert len(third) == 5

        # Perform a get_list filtered on a different field, then check the runtime field
        fourth = self.get_every_other_data_object(data_source)
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
        self.upsert_data_objects(
            data_source,
            ds_sleep,
            attributes=lambda id_: {
                'str_column': f'first_{id_}' if id_ % 3 == 0 else None,
                'str_column_2': f'second_{id_}' if id_ % 2 == 0 else None
            }
        )

        # Get by ID
        first = list(data_source.get_by_ids('root', ['1', '2', '6']))
        self.assert_correct_runtime_field_values(
            first,
            'coalesce_runtime_field',
            [
                # The first one should resolve to None because 1 is neither divisible by 2 nor 3
                None,
                # The second one should resolve to the value of `str_column_2`
                # because 2 is divisible by 2 but not by 3
                'second_2',
                # The third one should resolve to the value of `str_column` because 6 is divisible
                # by both 2 and 3, but `str_column` is the first in the field list
                'first_6'
            ]
        )

        # Get list by runtime field query.
        # As we're filtering the *coalesced* result, the only IDs that should resolve to the
        # second field are 2, 4, and 8.
        second = self.get_list_filtered(
            data_source,
            {'coalesce_runtime_field': {'contains': {'value': 'second'}}},
        )
        assert len(second) == 3

        # Do the same but with get_list_page
        third = self.get_list_filtered(
            data_source,
            {'coalesce_runtime_field': {'contains': {'value': 'second'}}},
            paged=True
        )
        assert len(third) == 3

        # Perform a get_list filtered on a different field, then check the runtime field
        fourth = self.get_every_other_data_object(data_source)
        self.assert_correct_runtime_field_values(
            fourth,
            'coalesce_runtime_field',
            [
                'first_0',   # id 0
                'second_2',  # id 2
                'second_4',  # id 4
                'first_6',   # id 6
                'second_8',  # id 8
            ]
        )

    @against(elastic, api_elastic)
    def test_math_function(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        self.upsert_data_objects(
            data_source,
            ds_sleep,
            attributes=lambda id_: {
                'int_column': 144,
                'double_column': float(id_)
            }
        )

        first = list(data_source.get_by_ids('root', ['0', '2', '6']))
        self.assert_correct_runtime_field_values(
            first[1:],  # Don't include ID 0 because of the zero-division issue
            'math_runtime_field',
            [
                # The first one is a division by zero.
                # TODO Return this as a value to display error in the UI.
                # For now, I've just removed ID 0.
                # We can't use pytest.raises for the division by zero here
                # because the error happens within the runtime field in Elastic.
                # ...
                # The second one should divide 144 by 2
                72,
                # The third one should divide 144 by 6
                24
            ]
        )

        # Get list by runtime field query.
        # 28.8 is 144/5, so it should include exactly half of the data objects
        # (as `gt` is non-inclusive)
        second = self.get_list_filtered(
            data_source,
            {'math_runtime_field': {'gt': {'value': 28.8}}},
        )
        assert len(second) == 5

        # Do the same but with get_list_page
        # (but this time we check for the other half)
        third = self.get_list_filtered(
            data_source,
            {'math_runtime_field': {'lt': {'value': 36}}},
            paged=True
        )
        assert len(third) == 5

        # Perform a get_list filtered on a different field, then check the runtime field
        fourth = self.get_every_other_data_object(data_source)
        self.assert_correct_runtime_field_values(
            fourth[1:],  # Don't include ID 0 because of the zero-division issue
            'math_runtime_field',
            [
                72,  # id 2
                36,  # id 4
                24,  # id 6
                18,  # id 8
            ]
        )

    @against(elastic, api_elastic)
    def test_min_function(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        self.upsert_data_objects(
            data_source,
            ds_sleep,
            attributes=lambda id_: {
                'int_column': 5,
                'double_column': float(id_)
            }
        )

        # Get by ID
        first = list(data_source.get_by_ids('root', ['1', '5', '8']))
        self.assert_correct_runtime_field_values(
            first,
            'min_runtime_field',
            [
                # For the first one, the ID is less than 5 so should take precedence
                1,
                # For the second one, they're the same value
                5,
                # For the third one, the ID is greater than 5
                5
            ]
        )

        # Get list by runtime field query.
        # Half of them should be less than 5 (as they're the min)
        second = self.get_list_filtered(
            data_source,
            {'min_runtime_field': {'lt': {'value': 5}}},
        )
        assert len(second) == 5

        # Do the same but with get_list_page
        # (but this time we check for the other half, so they should all be 5)
        third = self.get_list_filtered(
            data_source,
            {'min_runtime_field': {'eq': {'value': 5}}},
            paged=True
        )
        assert len(third) == 5

        # Perform a get_list filtered on a different field, then check the runtime field
        fourth = self.get_every_other_data_object(data_source)
        self.assert_correct_runtime_field_values(
            fourth,
            'min_runtime_field',
            [
                0,  # id 0
                2,  # id 2
                4,  # id 4
                5,  # id 6
                5,  # id 8
            ]
        )

    @against(elastic, api_elastic)
    def test_max_function(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        self.upsert_data_objects(
            data_source,
            ds_sleep,
            attributes=lambda id_: {
                'int_column': 5,
                'double_column': float(id_)
            }
        )

        # Get by ID
        first = list(data_source.get_by_ids('root', ['1', '5', '8']))
        self.assert_correct_runtime_field_values(
            first,
            'max_runtime_field',
            [
                # For the first one, the ID is less than 5 so should be overridden
                5,
                # For the second one, they're the same value
                5,
                # For the third one, the ID is greater than 5
                8
            ]
        )

        # Get list by runtime field query.
        # IDs 6 through 9 should have a maximum greater than 5.
        second = self.get_list_filtered(
            data_source,
            {'max_runtime_field': {'gt': {'value': 5}}},
        )
        assert len(second) == 4

        # Do the same but with get_list_page
        # IDs 0 through 5 should all have a maximum of 5.
        third = self.get_list_filtered(
            data_source,
            {'max_runtime_field': {'eq': {'value': 5}}},
            paged=True
        )
        assert len(third) == 6

        # Perform a get_list filtered on a different field, then check the runtime field
        fourth = self.get_every_other_data_object(data_source)
        self.assert_correct_runtime_field_values(
            fourth,
            'max_runtime_field',
            [
                5,  # id 0
                5,  # id 2
                5,  # id 4
                6,  # id 6
                8,  # id 8
            ]
        )

    @against(elastic, api_elastic)
    def test_date_interval_function(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        # Upsert objects with day intervals matching their IDs, crossing a leap day
        start = datetime(2020, 2, 27)
        self.upsert_data_objects(
            data_source,
            ds_sleep,
            attributes=lambda id_: {
                'datetime_column': start,
                'datetime_column_2': start + timedelta(days=id_)
            }
        )

        # Get by ID
        first = list(data_source.get_by_ids('root', ['0', '2', '6']))
        self.assert_correct_runtime_field_values(
            first,
            'date_interval_runtime_field',
            [
                # The first one has identical dates, so the interval should be zero
                0,
                # The second interval ends on the 29th of February, two days after the start
                2,
                # The third interval crosses into March and should be six days
                6
            ]
        )

        # Get list by runtime field query: half the intervals should be less than five days.
        second = self.get_list_filtered(
            data_source,
            {'date_interval_runtime_field': {'lt': {'value': 5}}},
        )
        assert len(second) == 5

        # Do the same with get_list_page, checking intervals of at least five days.
        third = self.get_list_filtered(
            data_source,
            {'date_interval_runtime_field': {'gte': {'value': 5}}},
            paged=True
        )
        assert len(third) == 5

        # Filter on a different field, then check the runtime field for the even IDs.
        fourth = self.get_every_other_data_object(data_source)
        self.assert_correct_runtime_field_values(
            fourth,
            'date_interval_runtime_field',
            [
                0,  # id 0
                2,  # id 2
                4,  # id 4
                6,  # id 6
                8,  # id 8
            ]
        )

    @against(elastic, api_elastic)
    def test_latest_date_function(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        # Upsert objects where either column can hold the latest date.
        # ID 0 has neither date, ID 1 only the first, and ID 2 only the second
        start = datetime(2020, 2, 27, tzinfo=timezone.utc)
        self.upsert_data_objects(
            data_source,
            ds_sleep,
            attributes=lambda id_: {
                'datetime_column': (
                    start + timedelta(days=id_) if id_ not in (0, 2) else None
                ),
                'datetime_column_2': (
                    start + timedelta(days=id_ - 1 if id_ % 2 == 0 else id_ + 1)
                    if id_ not in (0, 1) else None
                )
            }
        )

        # Get by ID: check missing dates, each single-date case, and both column orders.
        first = list(data_source.get_by_ids('root', ['0', '1', '2', '3', '4']))
        self.assert_correct_runtime_field_values(
            first,
            'latest_date_runtime_field',
            [
                # 0: Neither date exists, so the runtime field should be absent
                None,
                # 1, 2: The only date should be returned, regardless of which column contains it
                start + timedelta(days=1),
                start + timedelta(days=1),
                # 3, 4: ID 3 has a later second date, while ID 4 has a later first date
                start + timedelta(days=4),
                start + timedelta(days=4),
            ]
        )

        # Get list by runtime field query: IDs 1 through 4 have dates before day five.
        second = self.get_list_filtered(
            data_source,
            {'latest_date_runtime_field': {'lt': {'value': start + timedelta(days=5)}}},
        )
        assert len(second) == 4

        # Do the same with get_list_page, checking dates on or after day five.
        third = self.get_list_filtered(
            data_source,
            {'latest_date_runtime_field': {'gte': {'value': start + timedelta(days=5)}}},
            paged=True
        )
        assert len(third) == 5

        # Filter on a different field, then check the latest dates for the even IDs.
        fourth = self.get_every_other_data_object(data_source)
        self.assert_correct_runtime_field_values(
            fourth,
            'latest_date_runtime_field',
            [
                None,                       # id 0
                start + timedelta(days=1),  # id 2
                start + timedelta(days=4),  # id 4
                start + timedelta(days=6),  # id 6
                start + timedelta(days=8),  # id 8
            ]
        )

    @against(elastic, api_elastic)
    def test_substring_function(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        # Upsert strings whose first character is A for even IDs and B for odd IDs.
        # The remaining characters should not appear in the runtime field
        self.upsert_data_objects(
            data_source,
            ds_sleep,
            attributes=lambda id_: {
                'str_column': f'{"A" if id_ % 2 == 0 else "B"}_value_{id_}'
            }
        )

        # Get by ID
        first = list(data_source.get_by_ids('root', ['1', '2', '6']))
        self.assert_correct_runtime_field_values(
            first,
            'substring_runtime_field',
            [
                # The first string starts with B; the end index is exclusive.
                'B',
                # The second string starts with A.
                'A',
                # Different source strings with the same first character should
                # form the same substring
                'A'
            ]
        )

        # Get list by runtime field query: the five even IDs should resolve to A.
        second = self.get_list_filtered(
            data_source,
            {'substring_runtime_field': {'eq': {'value': 'A'}}},
        )
        assert len(second) == 5

        # Do the same with get_list_page, checking the odd IDs that resolve to B.
        third = self.get_list_filtered(
            data_source,
            {'substring_runtime_field': {'eq': {'value': 'B'}}},
            paged=True
        )
        assert len(third) == 5

        # Filter on a different field, then check the substring for the even IDs.
        fourth = self.get_every_other_data_object(data_source)
        self.assert_correct_runtime_field_values(
            fourth,
            'substring_runtime_field',
            [
                'A',  # id 0
                'A',  # id 2
                'A',  # id 4
                'A',  # id 6
                'A',  # id 8
            ]
        )

    @against(elastic, api_elastic)
    def test_substring_short_strings(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        """
        Empty and single-character strings must not fail the whole search
        """
        data_objects = [
            data_source.data_object_factory('root', str(id_), attributes={'str_column': value})
            for id_, value in enumerate(['', 'A', None])
        ]
        data_source.upsert('root', data_objects, provenance='source1')
        ds_sleep(2)

        objs = list(data_source.get_by_ids('root', ['0', '1', '2']))
        self.assert_correct_runtime_field_values(
            objs,
            'substring_runtime_field',
            ['', 'A', None]
        )

    @against(elastic, api_elastic)
    def test_concatenate_function(
        self,
        data_source: OperableDataSource,
        ds_sleep: Callable[[float], None]
    ):
        # Upsert strings with different prefixes for even and odd IDs.
        # Include the separator in the first field: concatenate should not add one
        self.upsert_data_objects(
            data_source,
            ds_sleep,
            attributes=lambda id_: {
                'str_column': 'even_' if id_ % 2 == 0 else 'odd_',
                'str_column_2': f'value_{id_}'
            }
        )

        # Get by ID
        first = list(data_source.get_by_ids('root', ['1', '2', '6']))
        self.assert_correct_runtime_field_values(
            first,
            'concatenate_runtime_field',
            [
                # The first string should precede the second, with no extra separator
                'odd_value_1',
                # The second object should use the even prefix
                'even_value_2',
                # The same prefix should still produce a distinct result
                # for a different second string
                'even_value_6'
            ]
        )

        # Get list by runtime field query: the five even IDs should have the even prefix.
        second = self.get_list_filtered(
            data_source,
            {'concatenate_runtime_field': {'contains': {'value': 'even_value_'}}},
        )
        assert len(second) == 5

        # Do the same with get_list_page, checking the odd prefix for the other half.
        third = self.get_list_filtered(
            data_source,
            {'concatenate_runtime_field': {'contains': {'value': 'odd_value_'}}},
            paged=True
        )
        assert len(third) == 5

        # Filter on a different field, then check the concatenated strings for the even IDs.
        fourth = self.get_every_other_data_object(data_source)
        self.assert_correct_runtime_field_values(
            fourth,
            'concatenate_runtime_field',
            [
                'even_value_0',  # id 0
                'even_value_2',  # id 2
                'even_value_4',  # id 4
                'even_value_6',  # id 6
                'even_value_8',  # id 8
            ]
        )
