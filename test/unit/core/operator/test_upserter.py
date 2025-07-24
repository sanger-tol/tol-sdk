# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable
from unittest.mock import create_autospec

from tol.core import DataObject
from tol.core.operator import Upserter

class TestUpserter:

    def test_upsert_arbitary_type(self) -> None:
        upserter: Upserter = create_autospec(
            Upserter,
            spec_set=True,
        )

        types_ = [
            'a',
            'a',
            'b',
            'a',
            'a',
            'a',
            'c',
            'c',
            'c',
            'c',
            'c',
        ]

        objs = self.__create_objs(types_)

        Upserter.upsert_arbitary_type(upserter, objs)

        self.__assert_correct(upserter)

    def __assert_correct(
        self,
        upserter: Upserter,
    ) -> None:

        expected = [
            2,  # a
            1,  # b
            3,  # a
            5,  # c
        ]

        observed = [
            len(list(iter_obj))
            for ((_, iter_obj,), _)
            in upserter.upsert.call_args_list
        ]

        assert observed == expected

    def __create_objs(
        self,
        types: Iterable[str],
    ) -> Iterable[DataObject]:

        return (
            self.__create_obj(type_, str(i))
            for i, type_ in enumerate(types)
        )

    def __create_obj(self, type_: str, id_: str) -> DataObject:
        obj: DataObject = create_autospec(
            DataObject,
            spec_set=True,
        )

        obj.type = type_
        obj.id = id_

        return obj
