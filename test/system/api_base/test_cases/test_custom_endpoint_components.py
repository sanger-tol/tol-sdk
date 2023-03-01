# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from ..models import HModelLog
from ..test_case import BaseTestCase


class TestCustomEndpointComponents(BaseTestCase):
    def test_create_log_base_object_using_dot(self):
        data = HModelLog(
            {'string_column': 'string_num_1'}
        )
        data.string_column = 'string_num_2'
        data.add(user_id=100)
        data.commit()

        # check object has been created
        self.assertTrue(
            isinstance(
                data.id,
                int
            )
        )
        # check column is populated
        self.assertEqual(
            data.string_column,
            'string_num_2'
        )
        # check log_base columns have been populated
        self.assertTrue(
            isinstance(
                data.created_by,
                int
            )
        )
        self.assertTrue(
            isinstance(
                data.created_at,
                datetime
            )
        )
        self.assertTrue(
            isinstance(
                data.last_modified_by,
                int
            )
        )
        self.assertTrue(
            isinstance(
                data.last_modified_at,
                datetime
            )
        )
        self.assertEqual(
            data.history,
            []
        )

    def test_create_log_base_object_using_update(self):
        data = HModelLog({
            'string_column': 'string_num_1'
        })
        data.update({
            'string_column': 'string_num_2'
        })
        data.add(user_id=100)
        data.commit()

        # check object has been created
        self.assertTrue(
            isinstance(
                data.id,
                int
            )
        )
        # check columns are populated
        self.assertEqual(
            data.string_column,
            'string_num_2'
        )
        # check log_base columns have been populated
        self.assertTrue(
            isinstance(
                data.created_by,
                int
            )
        )
        self.assertTrue(
            isinstance(
                data.created_at,
                datetime
            )
        )
        self.assertTrue(
            isinstance(
                data.last_modified_by,
                int
            )
        )
        self.assertTrue(
            isinstance(
                data.last_modified_at,
                datetime
            )
        )
        self.assertEqual(
            data.history,
            []
        )

    def test_update_log_base_object_using_dot(self):
        # create existing object
        original = HModelLog({
            'string_column': 'string_num_1'
        })
        original.save(user_id=100)

        # store original instance details
        prev_id = original.id
        prev_created_by = original.created_by
        prev_created_at = original.created_at
        prev_last_modified_at = original.last_modified_at

        # get existing object
        retrieved, _ = HModelLog.one_or_create({
            'string_column': 'string_num_1'
        })
        retrieved.string_column = 'string_num_2'
        retrieved.add(user_id=101)
        retrieved.commit()

        # check object ids are the same
        self.assertEqual(
            prev_id,
            retrieved.id
        )
        # check column is populated
        self.assertEqual(
            retrieved.string_column,
            'string_num_2'
        )

        # check log_base columns have been updated correctly
        self.assertEqual(
            prev_created_by,
            retrieved.created_by
        )
        self.assertEqual(
            prev_created_at,
            retrieved.created_at
        )
        self.assertNotEqual(
            prev_last_modified_at,
            retrieved.last_modified_at
        )
        self.assertTrue(
            isinstance(
                retrieved.last_modified_at,
                datetime
            )
        )
        self.assertEqual(
            retrieved.last_modified_by,
            101
        )

        # check an entry has been added to the history
        self.assertEqual(
            len(retrieved.history),
            1
        )
        self.assertEqual(
            retrieved.history[0]['data']['attributes']['string_column'],
            'string_num_1'
        )

    def test_update_log_base_object_using_update(self):
        # create existing object
        original = HModelLog({
            'string_column': 'string_num_1'
        })
        original.save(user_id=100)

        # store original instance details
        prev_id = original.id
        prev_created_by = original.created_by
        prev_created_at = original.created_at
        prev_last_modified_at = original.last_modified_at

        # get existing object
        retrieved, _ = HModelLog.one_or_create({
            'string_column': 'string_num_1'
        })
        retrieved.update({
            'string_column': 'string_num_2'
        })
        retrieved.add(user_id=101)
        retrieved.commit()

        # check object ids are the same
        self.assertEqual(
            prev_id,
            retrieved.id
        )
        # check column is populated
        self.assertEqual(
            retrieved.string_column,
            'string_num_2'
        )

        # check log_base columns have been updated correctly
        self.assertEqual(
            prev_created_by,
            retrieved.created_by
        )
        self.assertEqual(
            prev_created_at,
            retrieved.created_at
        )
        self.assertNotEqual(
            prev_last_modified_at,
            retrieved.last_modified_at
        )
        self.assertTrue(
            isinstance(
                retrieved.last_modified_at,
                datetime
            )
        )
        self.assertEqual(
            retrieved.last_modified_by,
            101
        )

        # check an entry has been added to the history
        self.assertEqual(
            len(retrieved.history),
            1
        )
        self.assertEqual(
            retrieved.history[0]['data']['attributes']['string_column'],
            'string_num_1'
        )
