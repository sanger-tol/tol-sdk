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
    'folder': {
        'attributes': {'name': 'str'},
        'to_one': {'parent_folder': 'folder'}
    },
    'worklist': {
        'attributes': {'name': 'str', 'worklist_type': 'str'}
    },
    'worklist_item': {
        'attributes': {'name': 'str'}
    },
    'transfer': {
        'attributes': {
            'source_entity_id': 'str',
            'destination_container_id': 'str'
        }
    },
    'assay_result': {
        'attributes': {}
    },
    'container_content': {
        'attributes': {
            'batch': 'str',
            'concentration': 'dict',
        },
        'to_one': {
            'entity': 'custom_entity',
        }
    }
}
BENCHLING_TYPE_SEARCH_WITH_SCHEMA_ID = [
    'custom_entity',
    'assay_result',
    'container',
    'plate',
    'box'
]

BENCHLING_PARENT_TYPES_WITH_SCHEMAS = {
    'custom_entity': {
        'attributes': {},
        'to_one': {},
        'to_one_native': {'folder': 'folder'},
        'to_many': {'container_contents': 'container_content'}
    },
    'location': {
        'attributes': {'name': 'str', 'barcode': 'str'},
        'to_one': {'parent_location': 'location'},
        'to_one_native': {},
        'to_many': {}
    },
    'assay_result': {
        'attributes': {},
        'to_one': {},
        'to_one_native': {},
        'to_many': {}
    },
    'container': {
        'attributes': {'barcode': 'str', 'parent_storage_id': 'str'},
        'to_one': {},
        'to_one_native': {},
        'to_many': {'container_contents': 'container_contents'}
    },
    'box': {
        'attributes': {'barcode': 'str'},
        'to_one': {'parent_storage_id': 'location'},
        'to_one_native': {},
        'to_many': {}
    },
    'plate': {
        'attributes': {'barcode': 'str'},
        'to_one': {'parent_storage_id': 'location'},
        'to_one_native': {},
        'to_many': {}
    },
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
        self.schemas = {
            benchling_type: self._get_schemas(benchling_type)
            for benchling_type in BENCHLING_PARENT_TYPES_WITH_SCHEMAS.keys()
        }

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

    def _get_schemas(
        self,
        benchling_type: str = 'custom_entity'
    ) -> dict[str, dict[str, dict[str, Any]]]:

        pages = self.__get_benchling_schema_function(benchling_type)()
        entities = {}
        for page in pages:
            for schema in page:
                if (
                    (
                        'assay_result' == benchling_type
                        or schema.registry_id == self.registry_id
                    )
                    and schema.archive_record is None
                ):
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
        if object_type in self.schemas['location'].keys():
            return self.benchling_interface.locations
        elif object_type in self.schemas['box'].keys():
            return self.benchling_interface.boxes
        elif object_type in self.schemas['plate'].keys():
            return self.benchling_interface.plates
        elif object_type in self.schemas['container'].keys():
            return self.benchling_interface.containers
        elif 'transfer' == object_type:
            return self.benchling_interface.containers
        else:
            match self.benchling_types[object_type]: # noqa E999
                case 'folder':
                    return self.benchling_interface.folders
                case 'worklist':
                    return self.benchling_interface.v2.beta.worklists
                case 'location':
                    return self.benchling_interface.locations
                case 'assay_result':
                    return self.benchling_interface.assay_results
                case _:
                    return self.benchling_interface.custom_entities

    def __get_benchling_schema_function(self, benchling_type: str):
        if benchling_type == 'custom_entity':
            return self.benchling_interface.schemas.list_entity_schemas
        function_name = f'list_{benchling_type}_schemas'
        func = getattr(self.benchling_interface.schemas, function_name)
        return func

    @ttl_cache(ttl=86400)
    def get_attribute_value_options(self, object_type: str, name: str) -> dict[str, str]:
        benchling_type = self.benchling_types[object_type]
        dropdown_id = self.schemas[benchling_type][object_type][name]['dropdown_id']
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
        """
            Update function of the benchling datasource

            Raises:
                Exception if the object_type is of the assay_result benchling_type.
                This is because the assay result does not support the update method
        """

        if 'assay_result' == self.benchling_types[object_type]:
            raise Exception('Update is not supported on the assay_result benchling_type')

        converter = self.__dc_factory()
        back_converter = self.__bc_factory()

        benchling_package = self.__get_benchling_package(object_type)
        if hasattr(benchling_package, 'bulk_update'):
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
        session=None,
        **kwargs,
    ) -> Iterable[DataObject | ErrorObject | None]:
        back_converter = self.__bc_factory()
        benchling_package = self.__get_benchling_package(object_type)
        benchling_type = self.benchling_types[object_type]
        try:
            kwargs = {}
            if benchling_type in BENCHLING_TYPE_SEARCH_WITH_SCHEMA_ID:
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
        session: Optional[OperableSession] = None,
        **kwargs,
    ) -> Iterable[DataObject]:
        # Currently only deals with filtering by eq/contains: name
        benchling_package = self.__get_benchling_package(object_type)
        benchling_type = self.benchling_types[object_type]
        kwargs = {}
        if object_filters is not None and object_filters.and_ is not None:
            if 'name' in object_filters.and_ and object_filters.and_['name'] is not None:
                if (
                        'contains' in object_filters.and_['name']
                        and object_filters.and_['name']['contains'] is not None
                        and 'value' in object_filters.and_['name']['contains']
                ):
                    kwargs['name_includes'] = object_filters.and_['name']['contains']['value']
                elif (
                    'eq' in object_filters.and_['name']
                    and object_filters.and_['name']['eq'] is not None
                    and 'value' in object_filters.and_['name']['eq']
                ):
                    kwargs['name'] = object_filters.and_['name']['eq']['value']

            if (
                'schema_fields' in object_filters.and_
                and object_filters.and_['schema_fields'] is not None
            ):
                kwargs['schema_fields'] = self.__build_schema_fields_filter(
                    object_filters.and_['schema_fields'],
                    object_type,
                    benchling_type
                )

            for key in ('barcodes', 'entity_ids'):
                if key in object_filters.and_ and object_filters.and_[key] is not None:
                    kwargs[key] = self.__build_list_filter(object_filters.and_[key])

        if benchling_type in BENCHLING_TYPE_SEARCH_WITH_SCHEMA_ID:
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
        except Exception as e:
            print(f'Exception type: {type(e)}')
            print(f'Exception message: {str(e)}')

    def delete(
        self,
        object_type: str,
        object_ids: Iterable[str],
        session=None
    ) -> None:
        benchling_package = self.__get_benchling_package(object_type)

        if hasattr(benchling_package, 'archive'):
            if (
                object_type in self.schemas['box'].keys()
                or object_type in self.schemas['plate'].keys()
                or object_type in self.schemas['container'].keys()
            ):
                benchling_package.archive(
                    object_ids,
                    reason=EntityArchiveReason.OTHER,  # may need to change this
                    should_remove_barcodes=True
                )
            elif object_type in self.schemas['assay_result'].keys():
                benchling_package.archive(
                    object_ids
                )
            else:
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

        bulk_create_method = None
        create_method = benchling_package.create
        if benchling_package == self.benchling_interface.assay_results:
            bulk_create_method = benchling_package.create
        elif 'transfer' == object_type:
            bulk_create_method = benchling_package.transfer_into_containers
            create_method = benchling_package.transfer_into_containers
        elif hasattr(benchling_package, 'bulk_create'):
            bulk_create_method = benchling_package.bulk_create

        if bulk_create_method is not None:
            # Do bulk inserts of object that allow it
            return self.__do_bulk_method(
                object_type,
                objects,
                converter,
                back_converter,
                bulk_create_method,
                create_method
            )
        else:
            # Other objects are inserted one-by-one
            return [
                self.__do_single_method(
                    object_type,
                    obj,
                    converter,
                    back_converter,
                    create_method
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
                converted_object = converter.convert_update(obj, object_type)
                # Need to pass in IDs for updates
                ret = method(obj[0], converted_object)
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
            converted_objects = converter.convert_bulk(page, object_type)
        else:
            converted_objects = converter.convert_bulk_update(page, object_type)

        if 'assay_result' == self.benchling_types[object_type]:
            response = bulk_method(converted_objects)

            if hasattr(response, '_errors'):
                return self.__retry_bulk_methods_on_singletons(
                    object_type,
                    page,
                    converter,
                    back_converter,
                    single_method
                )

            return_objects = [response]
        else:
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

            return_key = 'customEntities'
            if object_type in self.schemas['container'].keys():
                return_key = 'containers'
            elif 'transfer' == object_type:
                return_key = 'destinationContainers'

            return_objects = task.response.additional_properties[return_key]
        return back_converter.convert_return_entities(return_objects)

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
            } | BENCHLING_PARENT_TYPES_WITH_SCHEMAS[benchling_type]['attributes']
            for benchling_type in BENCHLING_PARENT_TYPES_WITH_SCHEMAS.keys()
            for k1, v1 in self.schemas[benchling_type].items()
        } | {
            k: v['attributes']
            for k, v in NATIVE_OBJECT_TYPES.items()
        }

    @property
    def supported_types(self) -> List:
        result = [
            key
            for benchling_type in BENCHLING_PARENT_TYPES_WITH_SCHEMAS.keys()
            for key in self.schemas[benchling_type].keys()
        ]
        result.extend(list(NATIVE_OBJECT_TYPES.keys()))
        return result

    @property
    def schema_ids(self) -> dict[str, str]:
        """
        Maps elements of `supported_types` to their
        `schema_id` in benchling.
        """

        return {
            k: v['__id__']
            for benchling_type in BENCHLING_PARENT_TYPES_WITH_SCHEMAS.keys()
            for k, v
            in self.schemas[benchling_type].items()
        }

    @property
    def schema_names(self) -> dict[str, str]:
        return {
            v['__id__']: k
            for benchling_type in BENCHLING_PARENT_TYPES_WITH_SCHEMAS.keys()
            for k, v
            in self.schemas[benchling_type].items()
        }

    @property
    def benchling_types(self) -> dict[str, str]:
        return {
            k: benchling_type
            for benchling_type in BENCHLING_PARENT_TYPES_WITH_SCHEMAS.keys()
            for k in self.schemas[benchling_type].keys()
        } | {k: k for k in NATIVE_OBJECT_TYPES.keys()}

    def get_page_size(self) -> int:
        return 20

    def __get_one_by_id(
        self,
        object_type: str,
        object_id: str
    ) -> BenchlingReturn:

        benchling_package = self.__get_benchling_package(object_type)
        benchling_type = self.benchling_types[object_type]
        try:
            if benchling_type in BENCHLING_TYPE_SEARCH_WITH_SCHEMA_ID:
                obj = benchling_package.get_by_id(
                    object_id,
                )
                if snakecase(obj.schema.name) == object_type:
                    return obj
                return None

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
                    'item': list(self.schemas['custom_entity'].keys())
                    + list(self.schemas['container'].keys()),
                }
            ),
            'container_content': RelationshipConfig(
                to_one={
                    'entity': list(self.schemas['custom_entity'].keys()),
                    'container': list(self.schemas['container'].keys()),
                },
                to_many={}
            )
        } | {
            k: RelationshipConfig(
                to_one={
                    attribute_name: self.schema_names.get(entity_def['schema_id'])
                    for attribute_name, entity_def in v.items()
                    if 'schema_id' in entity_def and entity_def['is_multi'] is False
                } | {
                    k1: list(self.schemas[v1].keys())
                    for k1, v1 in BENCHLING_PARENT_TYPES_WITH_SCHEMAS[benchling_type][
                        'to_one'
                    ].items()
                } | BENCHLING_PARENT_TYPES_WITH_SCHEMAS[benchling_type]['to_one_native'],
                to_many=BENCHLING_PARENT_TYPES_WITH_SCHEMAS[benchling_type]['to_many']
            )
            for benchling_type in BENCHLING_PARENT_TYPES_WITH_SCHEMAS.keys()
            for k, v in self.schemas[benchling_type].items()
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
            yield from back_converter.convert_worklist_items(
                self.__get_benchling_package('worklist').get_by_id(source.id)
            )

        if (
            source.type in self.schemas['container'].keys()
            and relationship_name == 'container_contents'
        ):
            back_converter = self.__bc_factory()
            contents = self.get_container_contents(source.id)
            yield back_converter.convert_container_contents(contents)

        if (
            source.type in self.schemas['custom_entity'].keys()
            and relationship_name == 'container_contents'
        ):
            back_converter = self.__bc_factory()
            container_list = self.benchling_interface.containers.list(
                storage_contents_id=source.id
            )
            for container in container_list:
                for individual_container in container:
                    converted_container = back_converter.convert(individual_container)
                    contents = self.get_container_contents(converted_container.id)
                    converted_contents = back_converter.convert_container_contents(contents)
                    for content in converted_contents:
                        if content.to_one_relationships['entity'].id == source.id:
                            yield content

    def __build_list_filter(self, list_filter: Optional[DataSourceFilter]):
        arg = ''

        if (
            'eq' in list_filter
            and list_filter['eq'] is not None
            and 'value' in list_filter['eq']
            and list_filter['eq']['value'] is not None
        ):
            arg = [list_filter['eq']['value']]
        elif (
            'in_list' in list_filter
            and list_filter['in_list'] is not None
            and 'value' in list_filter['in_list']
            and list_filter['in_list']['value'] is not None
            and isinstance(list_filter['in_list']['value'], list)
        ):
            arg = list_filter['in_list']['value']

        return arg

    def __build_schema_fields_filter(
        self,
        schema_filters: Optional[DataSourceFilter],
        object_type: str,
        benchling_type: str
    ):
        kwargs = {}

        if self.attribute_types.get(object_type):
            fields = self.schemas[benchling_type][object_type]

            for key, field_data in fields.items():
                filter_criteria = schema_filters.and_.get(key)

                if not filter_criteria:
                    continue

                field_type = field_data['type']

                # benchling expexts the field name as the key for the filter
                field_key = field_data['name']

                eq_value = filter_criteria.get('eq', {}).get('value')
                if field_type == 'str' and eq_value is not None:
                    benchling_data_type = field_data['benchling_type']

                    if benchling_data_type == 'dropdown':
                        options = self.get_attribute_value_options(object_type, key)
                        for identifier, option in options.items():
                            if option == eq_value:
                                eq_value = identifier
                                break

                    kwargs[field_key] = eq_value
                elif field_type in ['int', 'datetime', 'float']:
                    if eq_value is not None:
                        kwargs[field_key] = eq_value
                    else:
                        gt_eq_value = filter_criteria.get('gt_eq', {}).get('value')
                        ls_eq_value = filter_criteria.get('ls_eq', {}).get('value')
                        between_values = filter_criteria.get('between', {})

                        if gt_eq_value:
                            kwargs[field_key] = f'>={gt_eq_value}'
                        elif ls_eq_value:
                            kwargs[field_key] = f'<={ls_eq_value}'
                        elif (
                            'value_smaller' in between_values
                            and 'value_larger' in between_values
                        ):
                            kwargs[field_key] = (
                                f">={between_values['value_smaller']}"
                                f"<={between_values['value_larger']}"
                            )

        return kwargs

    def __clean_object_type(self, object_type):
        if object_type in self.benchling_types:
            return self.benchling_types[object_type]

        return object_type

    def get_container_contents(self, container_id):
        container_package = self.benchling_interface.containers

        return container_package.list_contents(container_id)
