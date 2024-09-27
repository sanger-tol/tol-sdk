# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import datetime
import typing
from typing import Any, Iterable
from uuid import uuid4

from benchling_api_client.models.naming_strategy import NamingStrategy

from benchling_sdk.helpers.serialization_helpers import fields
from benchling_sdk.models import (
    CustomEntity,
    CustomEntityBulkCreate,
    CustomEntityBulkUpdate,
    Fields
)

from caseconverter import snakecase

from ..core import Converter, DataDict, DataObject, DataSourceUpdate

if typing.TYPE_CHECKING:
    from .benchling_datasource import BenchlingDataSource


BenchlingReturn = dict[str, dict[str, Any]]
"""Returned from `insert` and `update` internally"""
BenchlingCreate = CustomEntityBulkCreate
"""Suitable as arguments to `insert`"""
BenchlingUpdate = CustomEntityBulkUpdate
"""Suitable as arguments to `update`"""
BenchlingWrite = BenchlingCreate | BenchlingUpdate
"""Suitable as arguments to either `insert` or `update`"""
BenchlingGet = CustomEntity
"""Returned by the `get_` methods - which are only for debugging!"""


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

    def convert(self, input_: BenchlingGet) -> DataObject:
        object_type = snakecase(input_.schema.name)
        return self.__ds.data_object_factory(
            object_type,
            id_=input_.id,
            attributes=self.__convert_attributes(input_.fields)
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
        }


class DataObjectConverter(Converter[DataObject, BenchlingWrite]):

    def __init__(
        self,
        benchling_ds: BenchlingDataSource
    ) -> None:

        self.__ds = benchling_ds

        super().__init__()

    def convert(self, input_: DataObject) -> BenchlingCreate:
        entity_fields = self.__convert_entity_fields(
            input_.type,
            input_.attributes
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
    ) -> BenchlingUpdate:

        update_id, update_dict = update

        entity_fields = self.__convert_entity_fields(
            object_type,
            update_dict
        )

        return CustomEntityBulkUpdate(
            id=update_id,
            fields=entity_fields,
            custom_fields=fields({})
        )

    def __convert_entity_fields(
        self,
        object_type: str,
        data_dict: DataDict
    ) -> Fields:

        mapped_dict = {
            self.__get_entity_name(object_type, name): {'value': self.__format_date(value)}
            for name, value in data_dict.items()
            if self.__ds.entities[object_type][name]['benchling_type'] != 'dropdown'
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
        return fields(mapped_dict | dropdown_values)

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
