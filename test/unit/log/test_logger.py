# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock, create_autospec

from tol.core import DataSource
from tol.core.operator import Deleter, Updater, Upserter
from tol.log import Logger


class _UpsertDataSource(DataSource, Upserter):
    """Has all required ABC's for a logging DataSource"""


class _Modifier(Deleter, Updater, Upserter):
    """A `DataSource` that has all unsafe, modifying methods"""


class TestLogger:
    """Tests the logger class"""

    def test_none_user_id(self):
        """got `user_id` is `None` -> don't log"""

        mock_upserter = create_autospec(_UpsertDataSource)
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

        mock_upserter = create_autospec(_UpsertDataSource)
        mock_upserter.data_object_factory.side_effect = self.__assert_correct_object(
            'log-fun_app',
            'test',
            'test-uuid',
            'datetime lol',
            'a-fun-user-ID',
            'delete'
        )
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

    def test_update_log(self):
        """`user_id` is set and not `None` -> log update"""

        mock_upserter = create_autospec(_UpsertDataSource)
        mock_upserter.data_object_factory.side_effect = self.__assert_correct_object(
            'log-fun_app',
            'test',
            'test-uuid',
            'datetime lol',
            'a-fun-user-ID',
            'update'
        )
        logger = Logger(
            mock_upserter,
            'fun_app',
            lambda: 'a-fun-user-ID',
            datetime_now=lambda: 'datetime lol',
            uuid_generator=lambda: 'test-uuid'
        )

        mock_updater = create_autospec(Updater)
        logger.register(mock_updater)

        # call the `update()` method
        mock_updater.update('test', [Mock()])

        # assert called once, with correct arguments
        mock_upserter.upsert.assert_called_once()

    def test_upsert_log(self):
        """`user_id` is set and not `None` -> log upsert"""

        mock_upserter_logger = create_autospec(_UpsertDataSource)
        mock_upserter_logger.data_object_factory.side_effect = self.__assert_correct_object(
            'log-fun_app',
            'test',
            'test-uuid',
            'datetime lol',
            'a-fun-user-ID',
            'upsert'
        )
        logger = Logger(
            mock_upserter_logger,
            'fun_app',
            lambda: 'a-fun-user-ID',
            datetime_now=lambda: 'datetime lol',
            uuid_generator=lambda: 'test-uuid'
        )

        mock_upserter = create_autospec(Upserter)
        logger.register(mock_upserter)

        # call the `upsert()` method
        mock_upserter.upsert('test', [Mock()])

        # assert called once, with correct arguments
        mock_upserter_logger.upsert.assert_called_once()
        print (mock_upserter_logger.upsert.call_args_list)
        assert False

    def __assert_correct_object(
        self,
        type_: str,
        _object_type_: str,
        _id_: str,
        datetime_: str,
        user_id_: str,
        operation_: str
    ) -> None:
        """
        Asserts that the data object given to the logging datasource's upsert
        is correct.
        """

        def inner(object_type: str, id_: str = None, data: dict = None) -> None:
            assert object_type == type_

            assert _id_ == id_
            assert data == {
                '_object_type': _object_type_,
                'datetime': datetime_,
                'user_id': user_id_,
                'operation': operation_
            }

        return inner
