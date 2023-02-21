# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from sqlalchemy.exc import MultipleResultsFound

from ..models import CModelWithNullableColumn
from ..test_case import BaseTestCase


class TestOneOrCreate(BaseTestCase):
    def test_existing_with_id(self):
        self.add_c(
            id=301,
            nullable_column='this_is_a_column_one',
            other_column='this_is_a_column_two'
        )
        data, new = CModelWithNullableColumn.one_or_create({
            'id': 301,
        })
        # check both columns at once
        self.assertEqual(
            data.nullable_column + data.other_column,
            'this_is_a_column_one' + 'this_is_a_column_two'
        )
        # object already existed
        self.assertFalse(new)

    def test_creation_with_id(self):
        data, new = CModelWithNullableColumn.one_or_create({
            'id': 301,
        })
        # check object is created
        self.assertEqual(
            data.id,
            301
        )
        # check another column is None
        self.assertEqual(
            data.other_column,
            None
        )
        # object is new
        self.assertTrue(new)

    def test_existing_with_composite_key(self):
        self.add_c(
            id=301,
            nullable_column='this_is_a_column_one',
            other_column='this_is_a_column_two'
        )
        data, new = CModelWithNullableColumn.one_or_create({
            'nullable_column': 'this_is_a_column_one',
            'other_column': 'this_is_a_column_two'
        })
        # check object id is the same
        self.assertEqual(
            data.id,
            301
        )
        # check both columns at once
        self.assertEqual(
            data.nullable_column + data.other_column,
            'this_is_a_column_one' + 'this_is_a_column_two'
        )
        self.assertFalse(new)

    def test_creation_with_composite_key(self):
        data, new = CModelWithNullableColumn.one_or_create({
            'nullable_column': 'this_is_a_column_one',
            'other_column': 'this_is_a_column_two'
        })
        # check new object id is still None until object is added
        self.assertEqual(
            data.id,
            None
        )
        # check new object id is created after adding object
        data.add()
        self.assertEqual(
            type(data.id),
            int
        )
        # check both columns at once
        self.assertEqual(
            data.nullable_column + data.other_column,
            'this_is_a_column_one' + 'this_is_a_column_two'
        )
        # object is new
        self.assertTrue(new)

    def test_creation_with_optional_data_added(self):
        data, new = CModelWithNullableColumn.one_or_create(
            {
                'nullable_column': 'this_is_a_column_one',
            },
            data={
                'other_column': 'this_is_a_column_two'
            }
        )
        # check new object id is still None until object is added
        self.assertEqual(
            data.id,
            None
        )
        # check new object id is created after adding object
        data.add()
        self.assertEqual(
            type(data.id),
            int
        )
        # check both columns at once
        self.assertEqual(
            data.nullable_column + data.other_column,
            'this_is_a_column_one' + 'this_is_a_column_two'
        )
        # object is new
        self.assertTrue(new)

    def test_candidate_key_overrides_data_with_object_creation(self):
        data, new = CModelWithNullableColumn.one_or_create(
            {
                'nullable_column': 'this_is_a_column_one',
                'other_column': 'this_is_a_column_two'
            },
            data={
                'other_column': 'we_do_not_want_this_used'
            }
        )
        # check new object id is still None until object is added
        self.assertEqual(
            data.id,
            None
        )
        # check new object id is created after adding object
        data.add()
        self.assertEqual(
            type(data.id),
            int
        )
        # check both columns at once
        self.assertEqual(
            data.nullable_column + data.other_column,
            'this_is_a_column_one' + 'this_is_a_column_two'
        )
        # object is new
        self.assertTrue(new)

    def test_fail_on_multiple_in_db(self):
        self.add_c(
            id=301,
            other_column='copy_entry'
        )
        self.add_c(
            id=302,
            other_column='copy_entry'
        )
        with pytest.raises(MultipleResultsFound):
            CModelWithNullableColumn.one_or_create({
                'other_column': 'copy_entry',
            }),

    def test_fail_on_none(self):
        with pytest.raises(Exception):
            CModelWithNullableColumn.one_or_create(None)
