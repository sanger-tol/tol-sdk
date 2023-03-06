# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from __future__ import annotations
from typing import List


class Queryable(ABC):
    """
    This abstract class is the main interface
    between types. It implements single and bulk
    methods of CRUD-operations and a few other
    useful ones.
    """

    @abstractmethod
    def get(self, id: str, *args, **kwargs) -> Queryable:
        pass

    @abstractmethod
    def get_bulk(self, *args, **kwargs) -> List[Queryable]:
        pass

    @abstractmethod
    def create(self, *args, **kwargs) -> Queryable:
        pass

    @abstractmethod
    def create_bulk(self, *args, **kwargs) -> List[Queryable]:
        pass

    @abstractmethod
    def update(self, id: str, *args, **kwargs) -> Queryable:
        pass

    @abstractmethod
    def update_bulk(self, *args, **kwargs) -> List[Queryable]:
        pass

    @abstractmethod
    def delete(self, id: str, *args, **kwargs) -> Queryable:
        pass

    @abstractmethod
    def delete_bulk(self, *args, **kwargs) -> List[Queryable]:
        pass

    @abstractmethod
    def upsert(self, *args, **kwargs) -> Queryable:
        pass

    @abstractmethod
    def upsert_bulk(self, *args, **kwargs) -> List[Queryable]:
        pass
