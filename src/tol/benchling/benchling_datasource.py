# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
import typing
from itertools import chain
from typing import Any, Callable, Iterable, List, Optional

from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.benchling import Benchling
from benchling_sdk.errors import BenchlingError, WaitForTaskExpiredError
from benchling_sdk.helpers.retry_helpers import RetryStrategy
from benchling_sdk.models import AsyncTask, AsyncTaskLink, EntityArchiveReason

from cachetools.func import ttl_cache

from caseconverter import snakecase

from more_itertools import batched

from .benchling_converter import (
    BenchlingConverter,
    BenchlingReturn,
    BenchlingWrite,
    DataObjectConverter
)
from ..core import (
    DataObject,
    DataSource,
    DataSourceConfig,
    DataSourceError,
    DataSourceFilter,
    ErrorObject
)
from ..core.operator import (
    Deleter,
    DetailGetter,
    Inserter,
    ListGetter,
    Relational,
    Updater
)
from ..core.operator.updater import DataObjectUpdate
from ..core.relationship import RelationshipConfig

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession

TYPE_MAPPING = {
    'text': 'str',
    'integer': 'int',
    'date': 'datetime',
    'float': 'float',
    'dropdown': 'str',
    'storage_link': 'str',
    'blob_link': 'str',
    'dna_sequence_link': 'str'
}
NATIVE_OBJECT_TYPES = {
    'folder': {'name': 'str'},
    'worklist': {'name': 'str', 'worklist_type': 'str'},
    'worklist_item': {'name': 'str'}
}

BenchlingConverterFactory = Callable[['BenchlingDataSource'], BenchlingConverter]
"""A type hint for the kwarg to `BenchlingDataSource`. Internally, there are no arguments."""
DataObjectConverterFactory = Callable[['BenchlingDataSource'], DataObjectConverter]
"""A type hint for the kwarg to `BenchlingDataSource`. Internally, there are no arguments."""


class BenchlingDataSource(
    DataSource,
    Deleter,
    DetailGetter,
    Inserter,
    ListGetter,
    Relational,
    Updater
):
    """
    A DataSource for writing objects to Benchling
    The queries are maintained in this SDK as SQL files
    """

    url: str
    api_key: str
    registry_id: str
    project_id: str

    def __init__(
        self,
        config: DataSourceConfig,
        benchling_converter_factory: BenchlingConverterFactory | None = None,
        data_object_converter_factory: DataObjectConverterFactory | None = None
    ) -> None:

        # initialy set to `None`
        self.__folder_id = None

        super().__init__(
            config,
            expected=[
                'url',
                'api_key',
                'registry_id',
                'project_id'
            ]
        )

        self.__init_factories(
            benchling_converter_factory,
            data_object_converter_factory,
        )

        self.benchling_interface = self._get_benchling_interface(self.url, self.api_key)
        self.entities = self._get_entity_schemas()

    @property
    def folder_id(self) -> str:
        """The current `folder_id` in Benchling"""

        return (
            self.__folder_id if
            self.__folder_id else
            os.getenv('BENCHLING_FOLDER')
        )

    @folder_id.setter
    def folder_id(self, new_id: str) -> None:
        self.__folder_id = new_id

    @folder_id.deleter
    def folder_id(self) -> None:
        self.__folder_id = None

    def _get_benchling_interface(self, url, api_key):
        return Benchling(
            url=url,
            auth_method=ApiKeyAuth(api_key),
            retry_strategy=RetryStrategy(
                max_tries=3,
                backoff_factor=60.0
            )
        )

    def _get_entity_schemas(
        self
    ) -> dict[str, dict[str, dict[str, Any]]]:

        pages = self.benchling_interface.schemas.list_entity_schemas(
            # registry_id=self.registry_id
        )
        entities = {}
        for page in pages:
            for schema in page:
                if schema.registry_id == self.registry_id \
                        and schema.archive_record is None:
                    schema_name = snakecase(schema.name)
                    entities[schema_name] = {
                        '__id__': schema.id
                    }
                    for field in schema.field_definitions:
                        if field.archive_record is None:
                            entities[schema_name][snakecase(field.name)] = {
                                'name': field.name,
                                'type': TYPE_MAPPING.get(field.type.value, 'str'),
                                'benchling_type': field.type.value,
                                'required': field.is_required,
                                'is_multi': field.is_multi
                            }
                            if field.type.value == 'dropdown':
                                entities[schema_name][snakecase(field.name)]['dropdown_id'] = \
                                    field.additional_properties.get('dropdownId')
                            if field.type.value == 'entity_link':
                                entities[schema_name][snakecase(field.name)]['schema_id'] = \
                                    field.additional_properties.get('schemaId')
        return entities

    def __get_benchling_package(self, object_type: str):
        if object_type == 'folder':
            return self.benchling_interface.folders
        if object_type == 'worklist':
            return self.benchling_interface.v2.beta.worklists
        return self.benchling_interface.custom_entities

    @ttl_cache(ttl=86400)
    def get_attribute_value_options(self, object_type: str, name: str) -> dict[str, str]:
        dropdown_id = self.entities[object_type][name]['dropdown_id']
        return {
            option.id: option.name
            for option in self.benchling_interface.dropdowns.get_by_id(dropdown_id).options
        }

    def update(
        self,
        object_type: str,
        updates: Iterable[DataObjectUpdate],
        **kwargs
    ) -> list[DataObject | ErrorObject]:

        converter = self.__dc_factory()
        back_converter = self.__bc_factory()

        benchling_package = self.__get_benchling_package(object_type)
        if object_type not in NATIVE_OBJECT_TYPES:
            return self.__do_bulk_method(
                object_type,
                updates,
                converter,
                back_converter,
                benchling_package.bulk_update,
                benchling_package.update
            )
        else:
            return [
                self.__do_single_method(
                    object_type,
                    update,
                    converter,
                    back_converter,
                    benchling_package.update
                )
                for update in updates
            ]

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        session=None
    ) -> Iterable[DataObject | ErrorObject | None]:
        back_converter = self.__bc_factory()
        benchling_package = self.__get_benchling_package(object_type)
        try:
            kwargs = {}
            if object_type not in NATIVE_OBJECT_TYPES:
                kwargs['schema_id'] = self.schema_ids[object_type]
            benchling_objects_page = benchling_package.list(
                ids=object_ids,
                **kwargs
            )
            for benchling_objects in benchling_objects_page:
                yield from self.sort_by_id(
                    back_converter.convert_iterable(benchling_objects),
                    object_ids
                )
        except BenchlingError:
            # Fall back to doing a one-by-one lookup
            for object_id in object_ids:
                benchling_object = self.__get_one_by_id(
                    object_type,
                    object_id
                )
                yield back_converter.convert(benchling_object) \
                    if benchling_object is not None else None

    def get_list(
            self,
            object_type: str,
            object_filters: Optional[DataSourceFilter] = None,
            session: Optional[OperableSession] = None
    ) -> Iterable[DataObject]:
        # Currently only deals with filtering by eq/contains: name
        benchling_package = self.__get_benchling_package(object_type)
        if object_filters is not None \
                and object_filters.and_ is not None \
                and 'name' in object_filters.and_ \
                and object_filters.and_['name'] is not None:
            if 'contains' in object_filters.and_['name'] \
                    and object_filters.and_['name']['contains'] is not None \
                    and 'value' in object_filters.and_['name']['contains']:
                kwargs = {
                    'name_includes': object_filters.and_['name']['contains']['value']
                }
            if 'eq' in object_filters.and_['name'] \
                    and object_filters.and_['name']['eq'] is not None \
                    and 'value' in object_filters.and_['name']['eq']:
                kwargs = {
                    'name': object_filters.and_['name']['eq']['value']
                }
        else:
            kwargs = {}
        if object_type not in NATIVE_OBJECT_TYPES:
            kwargs['schema_id'] = self.schema_ids[object_type]
        # Limit folder searching to the project set a top level
        if object_type == 'folder':
            kwargs['project_id'] = self.project_id

        back_converter = self.__bc_factory()
        try:
            benchling_objects_page = benchling_package.list(
                **kwargs
            )
            for benchling_objects in benchling_objects_page:
                yield from back_converter.convert_iterable(benchling_objects)
        except BenchlingError:
            return

    def delete(
        self,
        object_type: str,
        object_ids: Iterable[str],
        session=None
    ) -> None:
        benchling_package = self.__get_benchling_package(object_type)

        if hasattr(benchling_package, 'archive'):
            benchling_package.archive(
                object_ids,
                reason=EntityArchiveReason.OTHER  # may need to change this
            )
        elif hasattr(benchling_package, 'delete'):
            for object_id in object_ids:
                benchling_package.delete(object_id)
        else:
            raise DataSourceError(f'Cannot delete {object_type}')

    def insert(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        session=None,
        **kwargs
    ) -> list[DataObject | ErrorObject]:

        converter = self.__dc_factory()
        back_converter = self.__bc_factory()
        benchling_package = self.__get_benchling_package(object_type)
        if object_type == 'worklist_item':
            # Worklist items are appended to a worklist
            return self.__insert_worklist_items(
                objects,
                converter,
                back_converter
            )
        if object_type not in NATIVE_OBJECT_TYPES:
            # Do bulk inserts of custom entities
            return self.__do_bulk_method(
                object_type,
                objects,
                converter,
                back_converter,
                benchling_package.bulk_create,
                benchling_package.create,
            )
        else:
            # Native objects are inserted one-by-one
            return [
                self.__do_single_method(
                    object_type,
                    obj,
                    converter,
                    back_converter,
                    benchling_package.create
                )
                for obj in objects
            ]

    def __insert_worklist_items(
        self,
        objects: Iterable[DataObject],
        converter: DataObjectConverter,
        back_converter: BenchlingConverter
    ) -> list[DataObject | ErrorObject]:
        """
        Inserts worklist items into a worklist
        """
        for obj in objects:
            worklist_id = obj.worklist.id
            worklist_item_converted = converter.convert(obj)
            try:
                ret = self.__get_benchling_package('worklist').append_item(
                    worklist_id,
                    worklist_item_converted
                )
                yield back_converter.convert(ret)
            except BenchlingError as error:
                yield ErrorObject(
                    error.json['error']['message'],
                    'worklist_item',
                    http_code=error.status_code,
                    object_=obj
                )

    def __do_single_method(
        self,
        object_type: str,
        obj: DataObject,
        converter: DataObjectConverter,
        back_converter: BenchlingConverter,
        method: Callable[[BenchlingWrite], AsyncTaskLink]
    ) -> DataObject | ErrorObject:
        """
        Single object method
        """
        try:
            if isinstance(obj, DataObject):
                converted_object = converter.convert(obj)
                ret = method(converted_object)
            else:
                converted_object = converter.convert_update(
                    object_type,
                    obj
                )
                # Need to pass in IDs for updates
                ret = method(converted_object.id, converted_object)
            return back_converter.convert(ret)
        except BenchlingError as error:
            return ErrorObject(
                error.json['error']['message'],
                object_type,
                http_code=error.status_code,
                object_=obj
            )

    def __do_bulk_method(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        converter: DataObjectConverter,
        back_converter: BenchlingConverter,
        bulk_method: Callable[[Iterable[BenchlingWrite]], AsyncTaskLink] = None,
        single_method: Callable[[Iterable[BenchlingWrite]], AsyncTaskLink] = None
    ) -> list[DataObject | ErrorObject]:
        """
        Splits a (potentially long) `Iterable[DataObject]` into smaller
        pages lazily, and calls the given `bulk_method` (with retries)
        on each, chaining the results together.
        """
        batched_pages = batched(objects, 20)

        output_pages = (
            self.__do_bulk_method_on_page(
                object_type,
                list(page),
                converter,
                back_converter,
                bulk_method,
                single_method
            )
            for page in batched_pages
        )

        return list(
            chain.from_iterable(output_pages)
        )

    def __do_bulk_method_on_page(
        self,
        object_type: str,
        page: list[DataObject],
        converter,
        back_converter: BenchlingConverter,
        bulk_method: Callable[[Iterable[BenchlingWrite]], AsyncTaskLink],
        single_method: Callable[[Iterable[BenchlingWrite]], AsyncTaskLink],
    ) -> Iterable[DataObject | ErrorObject]:
        """
        Calls the given `bulk_method` on the `page` of `DataObject`
        instances.

        If this page fails, it is retried with each element
        individually.
        """

        if isinstance(page[0], DataObject):
            converted_objects = converter.convert_iterable(page)
        else:
            converted_objects = (
                converter.convert_update(
                    object_type,
                    obj
                )
                for obj in page
            )
        task = self.__wait_for_task(
            converted_objects,
            bulk_method
        )

        if task.status == 'FAILED':
            return self.__retry_bulk_methods_on_singletons(
                object_type,
                page,
                converter,
                back_converter,
                single_method
            )
        return back_converter.convert_return_entites(
            task.response.additional_properties['customEntities']
        )

    def __retry_bulk_methods_on_singletons(
        self,
        object_type: str,
        page: list[DataObject],
        converter: DataObjectConverter,
        back_converter: BenchlingConverter,
        single_method: Callable[[Iterable[BenchlingWrite]], AsyncTaskLink],
    ) -> list[DataObject | ErrorObject]:
        """
        Retries a failed page, iterating the bulk method
        on a singleton of each element.
        """
        for obj in page:
            yield self.__do_single_method(
                object_type,
                obj,
                converter,
                back_converter,
                single_method
            )

    def __wait_for_task(
        self,
        request: Iterable[BenchlingWrite],
        bulk_method: Callable[[Iterable[BenchlingWrite]], AsyncTaskLink],
    ) -> AsyncTask:

        try:
            response = bulk_method(request)
            return self.benchling_interface.tasks.wait_for_task(
                response.task_id,
                interval_wait_seconds=5
            )
        except WaitForTaskExpiredError:
            raise DataSourceError(
                'Time out in communication with Benchling '
                '(waiting for task response).',
                '',
                status_code=400
            )
        except BenchlingError as error:
            raise DataSourceError(
                'Error creating update task',
                error.json['error']['message'],
                status_code=400
            )

    @property
    def attribute_types(self):
        return {
            k1: {
                k2: v2['type']
                for k2, v2 in v1.items()
                if not k2.startswith('__')  # filter out '__id__'
                and v2['benchling_type'] != 'entity_link'
            }
            for k1, v1 in self.entities.items()
        } | NATIVE_OBJECT_TYPES

    @property
    def supported_types(self) -> List:
        return list(self.entities.keys()) + list(NATIVE_OBJECT_TYPES.keys())

    @property
    def schema_ids(self) -> dict[str, str]:
        """
        Maps elements of `supported_types` to their
        `schema_id` in benchling.
        """

        return {
            k: v['__id__']
            for k, v
            in self.entities.items()
        }

    @property
    def schema_names(self) -> dict[str, str]:
        return {
            v['__id__']: k
            for k, v
            in self.entities.items()
        }

    def get_page_size(self) -> int:
        return 20

    def __get_one_by_id(
        self,
        object_type: str,
        object_id: str
    ) -> BenchlingReturn:

        benchling_package = self.__get_benchling_package(object_type)
        try:
            if object_type not in NATIVE_OBJECT_TYPES:
                return benchling_package.get_by_id(
                    object_id,
                    schema_id=self.schema_ids[object_type]
                )
            return benchling_package.get_by_id(
                object_id
            )
        except BenchlingError:
            return None

    def __init_factories(
        self,
        benchling_converter_factory: BenchlingConverterFactory | None,
        data_object_converter_factory: DataObjectConverterFactory | None
    ) -> None:

        self.__bc_factory = (
            self.__default_bc_factory
            if benchling_converter_factory is None
            else lambda: benchling_converter_factory(self)
        )

        self.__dc_factory = (
            self.__default_dc_factory
            if data_object_converter_factory is None
            else lambda: data_object_converter_factory(self)
        )

    def __default_bc_factory(self) -> BenchlingConverter:
        return BenchlingConverter(self)

    def __default_dc_factory(self) -> DataObjectConverter:
        return DataObjectConverter(self)

    @property
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        """
        The configuration of relationships (both to-one and to-many) between
        the types of DataObject instances managed by this DataSource instance.
        """
        return {
            'folder': RelationshipConfig(
                to_one={
                    'parent_folder': 'folder'
                },
                to_many={}
            ),
            'worklist': RelationshipConfig(
                to_many={
                    'worklist_items': 'worklist_item'
                }
            ),
            'worklist_item': RelationshipConfig(
                to_one={
                    'worklist': 'worklist',
                    'item': list(self.entities.keys())
                }
            )
        } | {
            k: RelationshipConfig(
                to_one={
                    attribute_name: self.schema_names.get(entity_def['schema_id'])
                    for attribute_name, entity_def in v.items()
                    if 'schema_id' in entity_def and entity_def['is_multi'] is False
                },
                to_many={}
            )
            for k, v in self.entities.items()
        }

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str,
        session: Optional[OperableSession] = None
    ) -> Optional[DataObject]:
        """
        Gets the to-one relation DataObject, given a source DataObject and the
        name of the relationship within the config.
        """
        pass

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str,
        session: Optional[OperableSession] = None
    ) -> Iterable[DataObject]:
        """
        Gets the Iterable of to-many relation DataObject instances, given a source
        DataObject and the name of the relationship within the config.
        """
        if source.type == 'worklist' and relationship_name == 'worklist_items':
            back_converter = self.__bc_factory()
            return back_converter.convert_worklist_items(
                self.__get_benchling_package('worklist').get_by_id(source.id)
            )
