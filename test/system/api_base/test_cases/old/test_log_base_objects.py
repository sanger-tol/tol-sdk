# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from ...models import HModelLog
from ...schemas import HSchema
from ...test_case import BaseTestCase


class TestLogBaseObjects(BaseTestCase):
    def test_create_log_base_object(self):
        data = HModelLog({
            'string_column': 'string_is_here'
        })
        data.save(user_id=100)

        # check object has been created
        self.assertTrue(
            isinstance(
                data.id,
                int
            )
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

    def test_update_log_base_object(self):
        data = HModelLog({
            'id': 345
        })
        data.add(user_id=100)

        prev_created_by = data.created_by
        prev_created_at = data.created_at
        prev_last_modified_at = data.last_modified_at

        data.update(
            {'string_column': 'string_update!'},
            schema=HSchema,
            user_id=101
        )

        # check log_base columns have been updated correctly
        self.assertEqual(
            data.string_column,
            'string_update!'
        )
        self.assertEqual(
            prev_created_by,
            data.created_by
        )
        self.assertEqual(
            prev_created_at,
            data.created_at
        )
        self.assertNotEqual(
            prev_last_modified_at,
            data.last_modified_at
        )
        self.assertEqual(
            101,
            data.last_modified_by
        )
