# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing

from ..core import DataDict, DataObject

if typing.TYPE_CHECKING:
    from .api_datasource import ApiDataSource


class BadRelationshipException(Exception):
    pass


class ApiDataObject(DataObject):
    def __init__(
        self,
        object_type: str,
        data: DataDict = None,
        data_source: ApiDataSource = None
    ):
        self.__data_source = data_source
        super().__init__(object_type, data)
