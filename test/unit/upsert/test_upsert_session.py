# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

import pytest

from tol.core import CoreDataObject
from tol.upsert import Upserter
from tol.upsert.session import (
    UpsertSession,
    UpsertSessionExhaustedException
)


class TestUpsertSession:
    def test_upsert_one_type(self):
        mock_upserter, upsert_method_mock = self.__upserter_mock()
        objects = [
            CoreDataObject('test', {'id': i})
            for i in range(100)
        ]
        sess = UpsertSession(mock_upserter)
        sess.upsert(objects)
        sess.commit()
        self.__assert_upsert_call(upsert_method_mock, objects, None)

    def test_upsert_many_types(self):
        mock_upserter, upsert_method_mock = self.__upserter_mock()
        objects = [
            CoreDataObject(str(i), {'id': i, 'test': 'test'})
            for i in range(100)
        ]
        sess = UpsertSession(mock_upserter)
        sess.upsert(objects)
        sess.commit()
        self.__assert_upsert_call(upsert_method_mock, objects, None)

    def test_multiple_upserts_multiple_type(self):
        """
        Many upsert calls, multi-type mode, multiple types of object
        """
        mock_upserter, upsert_method_mock = self.__upserter_mock()
        objects = [
            CoreDataObject(str(i), {'id': i, 'test': 'test'})
            for i in range(100)
        ]
        sess = UpsertSession(mock_upserter)
        # do two separate upserts with the same objects twice
        sess.upsert(objects)
        sess.upsert(reversed(objects))
        sess.commit()
        # should be treated as one
        self.__assert_upsert_call(upsert_method_mock, [*objects, *reversed(objects)], None)

    def test_context_manager(self):
        mock_upserter, upsert_method_mock = self.__upserter_mock()
        objects = [
            CoreDataObject(str(i), {'id': i, 'test': 'test'})
            for i in range(100)
        ]
        # do two separate upserts with the same objects twice
        with UpsertSession(mock_upserter) as sess:
            sess.upsert(objects)
            sess.upsert(reversed(objects))
        # should have commited on leaving scope
        # should be treated as one
        self.__assert_upsert_call(upsert_method_mock, [*objects, *reversed(objects)], None)

    def test_mixed_iterable_types(self):
        mock_upserter, upsert_method_mock = self.__upserter_mock()
        objects_list = [
            CoreDataObject(str(i), {'id': i, 'test': 'test'})
            for i in range(100)
        ]
        # do two separate upserts with the same objects twice
        with mock_upserter.upsert_session() as sess:
            sess.upsert(reversed(objects_list))
            sess.upsert(objects_list)
        # should have commited on leaving scope
        # should be treated as one
        self.__assert_upsert_call(
            upsert_method_mock,
            [*reversed(objects_list), *objects_list],
            None
        )

    def test_many_iterables_single_type(self):
        """Many iterables in single-type mode"""
        mock_upserter, upsert_method_mock = self.__upserter_mock()
        objects_list = [
            CoreDataObject('single', {'id': i, 'test': 'test'})
            for i in range(100)
        ]
        reversed_objects = reversed(objects_list)
        # do two separate upserts with the same objects twice
        # use the session method of Upserter
        with mock_upserter.upsert_session(object_type='single') as sess:
            sess.upsert(reversed_objects)
            sess.upsert(objects_list)
        # the object_type is included in the call kwargs
        self.__assert_upsert_call(
            upsert_method_mock,
            [*reversed(objects_list), *objects_list],
            'single'
        )

    def test_commit_twice(self):
        """Calling commit twice raises UpsertSessionExhaustedException"""

        mock_upserter, _ = self.__upserter_mock()
        sess = mock_upserter.upsert_session()
        sess.commit()
        with pytest.raises(UpsertSessionExhaustedException):
            sess.commit()

    def test_with_and_additional_commit(self):
        """
        Exiting context and explicitly commiting after out of
        scope raises UpsertSessionExhaustedException
        """
        mock_upserter, _ = self.__upserter_mock()
        sess = mock_upserter.upsert_session()
        with sess:
            pass
        with pytest.raises(UpsertSessionExhaustedException):
            sess.commit()

    def test_commit_within_context(self):
        """
        Explicitly calling commit() within an UpsertSession context causes
        a UpsertSessionExhaustedException
        """
        mock_upserter, _ = self.__upserter_mock()
        with pytest.raises(UpsertSessionExhaustedException):
            with mock_upserter.upsert_session() as sess:
                sess.commit()

    def __upserter_mock(self):
        upsert_method_mock = MagicMock()
        mock_upserter = type(
            '',
            (Upserter,),
            {
                'upsert': upsert_method_mock
            }
        )()
        return mock_upserter, upsert_method_mock

    def __assert_upsert_call(self, upsert_method_mock: MagicMock, objects, object_type):
        upsert_method_mock.assert_called_once()
        ((upserts,), kwargs) = upsert_method_mock.call_args_list[0]
        assert list(upserts) == objects
        assert kwargs == {'object_type': object_type}
