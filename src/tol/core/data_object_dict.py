# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Iterable

from .data_object import DataObject


class DataObjectDict(dict):
    """
    A dictionary that supports an add method, taking a DataObjectABC
    instance, that filters into lists of the same (object) type.
    """

    def add(self, data_object: DataObject) -> None:
        """
        The given DataObject is added to the list of objects,
        grouped by object_type, with the common object_type as
        the key in this dict.
        """
        object_type = data_object.type
        data_objects = self.get(object_type, [])
        data_objects.append(data_object)
        self[object_type] = data_objects

    def add_bulk(self, data_objects: Iterable[DataObject]) -> None:
        """
        Functions like add(), but takes an iterable of data_objects and
        adds them sequentially.
        """
        for data_object in data_objects:
            self.add(data_object)
