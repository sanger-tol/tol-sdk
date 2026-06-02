# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, Iterable

from dateutil.parser import parse as dateutil_parse

from ..core import DataObject

if typing.TYPE_CHECKING:
    from ..core import DataSource


DummyResource = dict[str, Any]
DummyDoc = dict[str, list[DummyResource]]


class Parser(ABC):

    def parse_iterable(
        self,
        transfers: Iterable[DummyResource]
    ) -> Iterable[DataObject]:
        """
        Parses an `Iterable` of Dummy transfer resources
        """

        return (
            self.parse(t) for t in transfers
        )

    @abstractmethod
    def parse(self, transfer: DummyResource) -> DataObject:
        """
        Parses an individual Dummy transfer resource to a
        `DataObject` instance
        """


class DefaultParser(Parser):

    def __init__(self, data_source_dict: dict[str, DataSource]) -> None:
        self.__dict = data_source_dict

    def parse(self, transfer: DummyResource) -> DataObject:
        ds = self.__dict[transfer.get('type')]
        return ds.data_object_factory(
            transfer.get('type'),
            id_=transfer.get('id'),
            attributes={
                k: (
                    dateutil_parse(v)
                    if k in ['date'] and v is not None
                    else v
                )
                for k, v in transfer.items()
                if k not in ['id', 'type', 'category', 'sub_category']
            },
            to_one={
                'category': ds.data_object_factory(
                    'category',
                    transfer.get('category')
                ) if 'category' in transfer else None,
                'sub_category': ds.data_object_factory(
                    'sub_category',
                    transfer.get('sub_category')
                )  if 'sub_category' in transfer else None,
            }
        )
