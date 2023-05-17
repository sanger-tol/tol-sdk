# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, List, Optional

from ..api_client.dump import DumpedObject, UpsertDump
from ..core import DataObject


class LoadedDataObject(DataObject):
    """
    Implements the DataObject ABC using a transmitted
    serialisation.

    Provides a helper method to add relationships ex post
    facto.
    """

    def __init__(self, dumped_object: DumpedObject) -> None:
        self.__dumped_object = dumped_object
        self.__ones: Dict[str, DataObject] = {}
        self.__manys: Dict[str, List[DataObject]] = {}

    @property
    def type(self) -> str:  # noqa
        return self.__dumped_object['type']

    @property
    def id(self) -> Optional[str]:  # noqa
        return self.__dumped_object.get('id')

    @property
    def attributes(self) -> Dict[str, Any]:
        return self.__dumped_object.get('attributes', {})

    @property
    def to_one_relationships(self) -> Dict[str, DataObject]:
        return self.__ones

    @property
    def to_many_relationships(self) -> Dict[str, List[DataObject]]:
        return self.__manys

    @property
    def _request_uuid(self) -> str:
        return self.__dumped_object['_uuid']

    def configure_relationships(
        self,
        uuid_object_dict: Dict[str, DataObject]
    ) -> None:
        """
        Configures the relationships, given a mapping of UUID to
        DataObject instances.
        """
        self.__configure_ones(uuid_object_dict)
        self.__configure_manys(uuid_object_dict)

    def __configure_ones(
        self,
        uuid_object_dict: Dict[str, DataObject]
    ) -> None:
        for key, __uuid in self._one_uuids.items():
            data_object = uuid_object_dict[__uuid]
            self.__ones[key] = data_object

    def __configure_manys(
        self,
        uuid_object_dict: Dict[str, DataObject]
    ) -> None:
        for key, uuid_list in self._many_uuids.items():
            data_objects = [
                uuid_object_dict[__uuid]
                for __uuid in uuid_list
            ]
            self.__manys[key] = data_objects

    @property
    def _one_uuids(self) -> Dict[str, str]:
        """The mapping of to-one names and target UUID's."""
        return self.__relationships.get('one', {})

    @property
    def _many_uuids(self) -> Dict[str, List[str]]:
        """
        The mapping of to-many names and lists of target UUID's.
        """
        return self.__relationships.get('many', {})

    @property
    def __relationships(self) -> Dict[str, Any]:
        return self.__dumped_object.get('relationships', {})


class UpsertLoader:
    """
    Loads an upsert dump to an Iterable of DataObject instances,
    respecting the relationships between them.
    """

    def load(self, upsert_dump: UpsertDump) -> List[DataObject]:
        self.__loaded_objects = self.__load_objects(upsert_dump)
        self.__uuid_object_dict = self.__create_uuid_object_dict()
        self.__configure_relationships()
        return self.__loaded_objects

    def __load_objects(
        self,
        upsert_dump: UpsertDump
    ) -> List[LoadedDataObject]:
        return [
            LoadedDataObject(dumped_object)
            for dumped_object in upsert_dump['data']
        ]

    def __create_uuid_object_dict(self) -> Dict[str, LoadedDataObject]:
        return {
            o._request_uuid: o for o in self.__loaded_objects
        }

    def __configure_relationships(self) -> None:
        for data_object in self.__loaded_objects:
            data_object.configure_relationships(
                self.__uuid_object_dict
            )
