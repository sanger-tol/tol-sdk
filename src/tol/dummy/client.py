# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import string
from typing import Iterable, Optional

from .converter import DummyTransfer
from ..core import HttpClient


class DummyClient(HttpClient):
    """
    Simulates dummy objects retrieval from a remote API.
    """

    def __init__(
        self,
    ) -> None:
        super().__init__()

    def get_detail(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> Optional[DummyTransfer]:
        """
        Gets a list of Dummy transfers for the objects of specified
        `object_type` and `object_id`, or returns None if not found.
        """
        return self.__get_detail_data(object_type, object_ids)

    def get_list(
        self,
        object_type: str
    ) -> Optional[DummyTransfer]:
        return self.__get_detail_data(object_type, range(10000))

    def __get_detail_data(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> Optional[DummyTransfer]:
        if object_type == 'category':
            return self.__get_detail_category(object_type, object_ids)
        return self.__get_detail_record(object_type, object_ids)

    def __get_detail_record(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> Optional[DummyTransfer]:
        """
        Gets a list of dummy objects
        """
        ret = []
        for object_id in object_ids:
            if object_id < 10000:
                ret.append({
                    'id': object_id,
                    'little_string': ['a', 'b', 'c'][int(object_id) % 3],
                    'big_string': string.ascii_letters[int(object_id) % 52],
                    'int': object_id,
                    'bool': int(object_id) % 2 == 0,
                    'date': f'2024-01-{(int(object_id) % 28) + 1:02d}',
                    'type': object_type,
                    'category': ['cat1', 'cat2', 'cat3', 'cat4'][int(object_id) % 4],
                })
            else:
                ret.append(None)
        return ret

    def __get_detail_category(
        self,
        object_type: str,
        object_ids: Iterable[str]
    ) -> Optional[DummyTransfer]:
        """
        Gets a list of dummy objects
        """
        ret = []
        for object_id in object_ids:
            ret.append({
                'id': object_id,
                'name': object_id.upper(),
                'type': object_type
            })
        return ret
