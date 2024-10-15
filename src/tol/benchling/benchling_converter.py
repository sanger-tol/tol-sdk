# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import datetime
import typing
from typing import Any, Iterable
from uuid import uuid4

from benchling_api_client.models.naming_strategy import NamingStrategy
from benchling_api_client.v2.beta.models.worklist import Worklist
from benchling_api_client.v2.beta.models.worklist_create import WorklistCreate
from benchling_api_client.v2.beta.models.worklist_item import WorklistItem
from benchling_api_client.v2.beta.models.worklist_item_create import WorklistItemCreate
from benchling_api_client.v2.beta.models.worklist_type import WorklistType

from benchling_sdk.helpers.serialization_helpers import fields
from benchling_sdk.models import (
    CustomEntity,
    CustomEntityBulkCreate,
    CustomEntityBulkUpdate,
    Fields,
    Folder,
    FolderCreate,
)

from caseconverter import snakecase

from ..core import Converter, DataDict, DataObject, DataSourceError, DataSourceUpdate

if typing.TYPE_CHECKING:
    from .benchling_datasource import BenchlingDataSource


BenchlingReturn = dict[str, dict[str, Any]]
"""Returned from `insert` and `update` internally"""
BenchlingCustomEntityCreate = CustomEntityBulkCreate
"""Suitable as arguments to `insert`"""
BenchlingCustomEntityUpdate = CustomEntityBulkUpdate
"""Suitable as arguments to `update`"""
BenchlingCustomEntity = CustomEntity
"""Returned by the `get_` methods - which are only for debugging!"""
BenchlingFolder = Folder
BenchlingFolderCreate = FolderCreate
BenchlingWorklist = Worklist
BenchlingWorklistCreate = WorklistCreate
BenchlingWorklistItem = WorklistItem
BenchlingWorklistItemCreate = WorklistItemCreate
BenchlingObject = BenchlingCustomEntity | BenchlingFolder | BenchlingWorklist
BenchlingObjectCreate = BenchlingCustomEntityCreate | BenchlingFolderCreate \
    | BenchlingWorklistCreate | BenchlingWorklistItemCreate
BenchlingObjectUpdate = BenchlingCustomEntityUpdate
BenchlingWrite = BenchlingObjectCreate | BenchlingObjectUpdate
"""Suitable as arguments to either `insert` or `update`"""


class BenchlingConverter(Converter[BenchlingReturn, DataObject]):

    def __init__(
        self,
        benchling_ds: BenchlingDataSource
    ) -> None:

        self.__ds = benchling_ds

        super().__init__()

    def convert_return_entites(
        self,
        input_list: list[BenchlingReturn]
    ) -> Iterable[DataObject]:

        return (
            self.__convert_return(input_)
            for input_ in input_list
        )

    def convert(self, input_: BenchlingObject) -> DataObject:
        if isinstance(input_, BenchlingFolder):
            return self.__convert_folder(input_)
        elif isinstance(input_, BenchlingWorklist):
            return self.__convert_worklist(input_)
        elif isinstance(input_, BenchlingWorklistItem):
            return self.__convert_worklist_item(input_)
        elif isinstance(input_, BenchlingCustomEntity):
            return self.__convert_custom_entity(input_)
        raise ValueError(f'Unknown object type: {type(input_)}')

    def __convert_folder(self, input_: BenchlingFolder) -> DataObject:
        return self.__ds.data_object_factory(
            'folder',
            id_=input_.id,
            attributes={'name': input_.name},
            to_one={
                'parent_folder': self.__ds.data_object_factory(
                    'folder',
                    input_.parent_folder_id,
                    stub=True
                ) if input_.parent_folder_id is not None else None
            }
        )

    def __convert_worklist(self, input_: BenchlingWorklist) -> DataObject:
        return self.__ds.data_object_factory(
            'worklist',
            id_=input_.id,
            attributes={'name': input_.name}
        )

    def __convert_worklist_item(self, input_: BenchlingWorklistItem) -> DataObject:
        # Benchling gives back the object that has been added to the worklist
        # for now, we will return None
        return None

    def convert_worklist_items(self, worklist: BenchlingWorklist) -> Iterable[DataObject]:
        # This is a bit of a hack as we don't know exactly the type of the objects
        # in the worklist. More work will be needed here eventually
        worklist_type = worklist.type
        worklist_items = worklist.worklist_items
        for worklist_item in worklist_items:
            to_ones = {}
            if worklist_type == 'bioentity':
                to_ones = {
                    'tissue': self.__ds.data_object_factory(
                        'tissue',
                        id_=worklist_item.id,
                        stub=True
                    )
                }

            yield self.__ds.data_object_factory(
                'worklist_item',
                id_=f'{worklist.id}_{worklist_item.id}',
                attributes={
                    'name': worklist_item.name,
                },
                to_one=to_ones | {
                    'worklist': self.__ds.data_object_factory(
                        'worklist',
                        worklist.id,
                        stub=True
                    )
                }
            )

    def __convert_custom_entity(self, input_: BenchlingCustomEntity) -> DataObject:
        object_type = snakecase(input_.schema.name)
        return self.__ds.data_object_factory(
            object_type,
            id_=input_.id,
            attributes=self.__convert_attributes(input_.fields),
            to_one=self.__convert_relationships(input_.fields, object_type)
        )

    def __convert_return(self, input_: BenchlingReturn) -> DataObject:
        id_ = input_.pop('id', None)
        schema = input_.pop('schema', None)
        if schema is not None:
            object_type = snakecase(schema.get('name', None))

        return self.__ds.data_object_factory(
            object_type,
            id_=id_,
            attributes=self.__convert_return_attributes(
                input_
            ),
            to_one=self.__convert_return_relationships(
                input_,
                object_type
            )
        )

    def __convert_return_attributes(
        self,
        input_: BenchlingReturn
    ) -> dict[str, Any]:

        return {
            snakecase(k): v['value']
            for k, v
            in input_.get('fields', {}).items()
            if v['type'] != 'entity_link'
        }

    def __convert_return_relationships(
        self,
        input_: BenchlingReturn,
        object_type: str
    ) -> dict[str, Any]:

        return {
            snakecase(k): self.__ds.data_object_factory(
                self.__ds.schema_names[self.__ds.entities[object_type][snakecase(k)]['schema_id']],
                v['value'],
                stub=True
            )
            for k, v
            in input_.get('fields', {}).items()
            if v['type'] == 'entity_link'
        }

    def __convert_attributes(self, fields: Fields) -> dict[str, Any]:
        raw_attributes = self.__get_raw_attributes(fields)

        return self.__format_attributes(raw_attributes)

    def __get_raw_attributes(
        self,
        fields: Fields
    ) -> dict[str, dict[str, Any]]:

        fields_dict = fields.to_dict()
        additional_properties = fields_dict.pop('additional_properties', {})

        return {
            **fields_dict,
            **additional_properties
        }

    def __format_attributes(
        self,
        raw_attributes: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:

        return {
            snakecase(k): v.get('value')
            for k, v in raw_attributes.items()
            if v['type'] != 'entity_link'
        }

    def __convert_relationships(self, fields: Fields, object_type: str) -> dict[str, Any]:
        raw_attributes = self.__get_raw_attributes(fields)

        return self.__format_relationships(raw_attributes, object_type)

    def __format_relationships(
        self,
        raw_attributes: dict[str, dict[str, Any]],
        object_type: str
    ) -> dict[str, Any]:

        return {
            snakecase(k): self.__ds.data_object_factory(
                self.__ds.schema_names[self.__ds.entities[object_type][snakecase(k)]['schema_id']],
                v.get('value'),
                stub=True
            )
            for k, v in raw_attributes.items()
            if v['type'] == 'entity_link'
        }


class DataObjectConverter(Converter[DataObject, BenchlingWrite]):

    def __init__(
        self,
        benchling_ds: BenchlingDataSource
    ) -> None:

        self.__ds = benchling_ds

        super().__init__()

    def convert(self, input_: DataObject) -> BenchlingObjectCreate:
        if input_.type in self.__ds.entities.keys():
            return self.__convert_custom_entity(input_)
        if input_.type == 'folder':
            return self.__convert_folder(input_)
        if input_.type == 'worklist':
            return self.__convert_worklist(input_)
        if input_.type == 'worklist_item':
            return self.__convert_worklist_item(input_)
        raise ValueError(f'Unknown object type: {input_.type}')

    def __convert_folder(self, input_: DataObject) -> BenchlingFolderCreate:
        return FolderCreate(
            name=input_.name,
            parent_folder_id=input_.parent_folder.id if input_.parent_folder is not None else None
        )

    def __convert_worklist(self, input_: DataObject) -> BenchlingWorklistCreate:
        mappings = {
            'bioentity': WorklistType.BIOENTITY,
            'container': WorklistType.CONTAINER,
            'plate': WorklistType.PLATE,
            'batch': WorklistType.BATCH
        }
        return WorklistCreate(
            name=input_.name,
            type=mappings.get(input_.worklist_type, WorklistType.BIOENTITY)
        )

    def __convert_worklist_item(self, input_: DataObject) -> BenchlingWorklistItemCreate:
        return WorklistItemCreate(
            item_id=input_.tissue.id
        )

    def __convert_custom_entity(self, input_: DataObject) -> BenchlingCustomEntityCreate:
        entity_fields = self.__convert_entity_fields(
            input_.type,
            input_.attributes,
            input_.to_one_relationships
        )
        return CustomEntityBulkCreate(
            name=uuid4().hex,
            schema_id=self.__ds.schema_ids[input_.type],
            registry_id=self.__ds.registry_id,
            folder_id=self.__ds.folder_id,
            fields=entity_fields,
            naming_strategy=NamingStrategy.REPLACE_NAMES_FROM_PARTS,
            custom_fields=fields({})
        )

    def convert_update(
        self,
        object_type: str,
        update: DataSourceUpdate
    ) -> BenchlingObjectUpdate:
        # This function needs some work to handle objects other than custom_entities.
        # It would be better if we could just use convert() for updates as well.
        update_id, update_dict = update
        if object_type in self.__ds.entities.keys():
            entity_fields = self.__convert_entity_fields(
                object_type,
                update_dict
            )

            return CustomEntityBulkUpdate(
                id=update_id,
                fields=entity_fields,
                custom_fields=fields({})
            )
        raise DataSourceError('Cannot update object type {object_type}')

    def __convert_entity_fields(
        self,
        object_type: str,
        data_dict: DataDict,
        to_one_relationships: dict[str, DataObject] = {}
    ) -> Fields:
        mapped_dict = {
            self.__get_entity_name(object_type, name): {'value': self.__format_date(value)}
            for name, value in data_dict.items()
            if self.__ds.entities[object_type][name]['benchling_type'] != 'dropdown'
        }
        mapped_relationships = {
            self.__get_entity_name(object_type, name): {'value': value.id}
            for name, value in to_one_relationships.items()
            if value is not None  # Not sure how to handle null relationships
        }
        # Convert dropdown values to Benchling dropdown values
        dropdown_values = {
            self.__get_entity_name(object_type, name): {
                'value': next(
                    (k for k, v in self.__ds.get_attribute_value_options(object_type, name).items()
                     if v == value),
                    None
                )
            }
            for name, value in data_dict.items()
            if self.__ds.entities[object_type][name]['benchling_type'] == 'dropdown'
        }
        return fields(mapped_dict | mapped_relationships | dropdown_values)

    def __get_entity_name(
        self,
        object_type: str,
        name: str
    ) -> str:

        return self.__ds.entities[object_type][name]['name']

    def __format_date(self, date: Any) -> str:
        if isinstance(date, datetime.datetime):
            return date.isoformat()
        return date
