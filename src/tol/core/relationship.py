# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Dict, Optional

if typing.TYPE_CHECKING:
    from .data_object import DataObject
    from .datasource import DataSource


@dataclass
class RelationshipConfig:
    """
    Describes the configuration of relationships on a specific
    type of DataObject.

    The keys of each Optional[Dict] are the names of a relationship,
    and the values are the type of DataObject instances to which they
    are directed.
    """

    to_one: Optional[Dict[str, str]] = None
    to_many: Optional[Dict[str, str]] = None


class ToOneRelationshipDict(Mapping):
    """
    Lazily loads to-one relationship DataObject instances.
    """

    def __init__(
        self,
        parent: DataObject,
        data_source_dict: Dict[str, DataSource]
    ) -> None:
        self.__parent = parent
        self.__data_source_dict = data_source_dict

    def __getitem__(self, __k: str) -> Optional[DataObject]:
        pass

    def __setitem__(self, *args, **kwargs) -> None:
        raise NotImplementedError('This Dict is readonly.')

    def __len__(self) -> int:
        pass
