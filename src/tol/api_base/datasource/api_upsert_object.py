# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ...core import DataObject


class UnknownUuidError(Exception):
    def __init__(self, __uuid: str):
        super().__init__(
            f'No object exists in the request with UUID: "{__uuid}".'
        )


class ApiUpsertObject(DataObject):
    """
    A DataObjectABC implementation from an API transfer dictionary.
    """

    def __init__(self, json_dict: Dict[str, Any]):
        self.__json_dict = json_dict
        self.__to_one: Dict[str, ApiUpsertObject] = {}
        self.__to_many: Dict[str, List[ApiUpsertObject]] = {}

    @property
    def type(self) -> str:  # noqa
        return self.__json_dict['type']

    @property
    def id(self) -> Optional[str]:  # noqa
        return self.__json_dict.get('id')

    @property
    def attributes(self) -> Dict[str, Any]:
        return self.__json_dict.get('attributes', {})

    @property
    def to_one_relationships(self) -> Dict[str, DataObject]:
        return self.__to_one

    @property
    def to_many_relationships(self) -> Dict[str, List[DataObject]]:
        return self.__to_many

    @property
    def _internal_uuid(self) -> str:
        return self.__json_dict['_uuid']

    @property
    def _to_one_uuids(self) -> Dict[str, str]:
        relationships = self.__get_relationships()
        return relationships.get('one', {})

    @property
    def _to_many_uuids(self) -> Dict[str, List[str]]:
        relationships = self.__get_relationships()
        return relationships.get('many', {})

    def __get_relationships(self) -> Dict[str, Any]:
        return self.__json_dict.get('relationships', {})

    def add_to_many_relationship_object(
        self,
        relationship_name: str,
        data_object: DataObject
    ) -> None:
        """
        For a to-many relationship of the given name, either:

        - creates a new relationship list, if none already exists
        - adds the object to an existing relationship list
        """
        manys = self.__to_many.get(relationship_name, [])
        manys.append(data_object)
        self.__to_many[relationship_name] = manys

    def add_to_one_relationship_object(
        self,
        relationship_name: str,
        data_object: DataObject
    ) -> None:
        """
        Adds a to-one relationship of the given name.
        """
        self.__to_one[relationship_name] = data_object
