# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock, create_autospec

from tol.core.operator import Deleter, Updater, Upserter
from tol.log import Logger


class _Modifier(Deleter, Updater, Upserter):
    """A `DataSource` that has all unsafe, modifying methods"""


class TestLogger:
    """Tests the logger class"""

    def test_none_user_id(self):
        """got `user_id` is `None` -> don't log"""

        mock_upserter = create_autospec(Upserter)
        logger = Logger(
            mock_upserter,
            'fun_app',
            lambda: None,
            uuid_generator=lambda: 'test-uuid'
        )

        # a mock DataSource instance implementing all operators
        mock_ds = create_autospec(_Modifier)

        # register the `DataSource` with the `Logger` instance
        logger.register(mock_ds)

        # do all modifications
        mock_ds.delete('test', ['1', '2', '3'])
        mock_ds.upsert('test', [Mock(), Mock()])
        mock_ds.update('test', [Mock(), Mock()])

        # no upserts on the logging `DataSource` instance
        mock_upserter.upsert.assert_not_called()

    def test_delete_log(self):
        """`user_id` is set and not `None` -> log delete"""

        mock_upserter = create_autospec(Upserter)
        logger = Logger(
            mock_upserter,
            'fun_app',
            lambda: 'a-fun-user-ID',
            datetime_now=lambda: 'datetime lol',
            uuid_generator=lambda: 'test-uuid'
        )

        mock_deleter = create_autospec(Deleter)
        logger.register(mock_deleter)

        # call the `delete()` method
        mock_deleter.delete('test', ['thing_A'])

        # assert called once, with correct arguments
        mock_upserter.upsert.assert_called_once()
        ((log_object_type, (data_object,)), _) = mock_upserter.upsert.call_args_list
        assert log_object_type == 'log-fun_app'
        assert data_object.type == 'test'
        assert data_object.datetime == 'datetime lol'

    def test_update_log(self):
        """`user_id` is set and not `None` -> log update"""

    def test_upsert_log(self):
        """`user_id` is set and not `None` -> log upsert"""
