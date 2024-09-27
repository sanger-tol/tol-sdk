# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
from itertools import chain
from typing import Any, Callable, Iterable, List

from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.benchling import Benchling
from benchling_sdk.errors import BenchlingError, WaitForTaskExpiredError
from benchling_sdk.helpers.retry_helpers import RetryStrategy
from benchling_sdk.models import AsyncTask, AsyncTaskLink

from cachetools.func import ttl_cache

from caseconverter import snakecase

from more_itertools import batched

from tol.core.data_object import DataObject, ErrorObject

from .benchling_converter import (
    BenchlingConverter,
    BenchlingReturn,
    BenchlingWrite,
    DataObjectConverter
)
from ..core import (
    DataSource,
    DataSourceConfig,
    DataSourceError
)
from ..core.operator import Deleter, DetailGetter, Inserter, Updater
from ..core.operator.updater import DataObjectUpdate


TYPE_MAPPING = {
    'text': 'str',
    'integer': 'int',
    'date': 'datetime',
    'float': 'float',
    'dropdown': 'str',
    'entity_link': 'str',
    'storage_link': 'str',
    'blob_link': 'str',
    'dna_sequence_link': 'str'
}


BenchlingConverterFactory = Callable[['BenchlingDataSource'], BenchlingConverter]
"""A type hint for the kwarg to `BenchlingDataSource`. Internally, there are no arguments."""
DataObjectConverterFactory = Callable[['BenchlingDataSource'], DataObjectConverter]
"""A type hint for the kwarg to `BenchlingDataSource`. Internally, there are no arguments."""


class BenchlingDataSource(DataSource, Deleter, DetailGetter, Updater, Inserter):
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
                            }
                            if field.type.value == 'dropdown':
                                entities[schema_name][snakecase(field.name)]['dropdown_id'] = \
                                    field.additional_properties.get('dropdownId')
        return entities

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
        converted_updates = (
            converter.convert_update(
                object_type,
                update
            )
            for update in updates
        )
        back_converter = self.__bc_factory()

        return self.__do_bulk_method(
            object_type,
            converted_updates,
            back_converter,
            self.benchling_interface.custom_entities.bulk_update
        )

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        session=None
    ) -> Iterable[DataObject | ErrorObject | None]:

        back_converter = self.__bc_factory()

        # this isn't very efficient
        models = (
            self.__get_one_by_id(object_type, id_)
            for id_ in object_ids
        )

        return back_converter.convert_iterable(models)

    def delete(
        self,
        object_type: str,
        object_ids: Iterable[str],
        session=None
    ) -> None:

        self.benchling_interface.custom_entities.archive(
            object_ids
        )

    def insert(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        session=None,
    ) -> list[DataObject | ErrorObject]:

        converter = self.__dc_factory()
        back_converter = self.__bc_factory()

        return self.__do_bulk_method(
            object_type,
            converter.convert_iterable(objects),
            back_converter,
            self.benchling_interface.custom_entities.bulk_create
        )

    def __do_bulk_method(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        back_converter: BenchlingConverter,
        bulk_method: Callable[[Iterable[BenchlingWrite]], AsyncTaskLink],
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
                back_converter,
                bulk_method
            )
            for page in batched_pages
        )

        return list(
            chain.from_iterable(output_pages)
        )

    def __do_bulk_method_on_page(
        self,
        object_type: str,
        page: list[BenchlingWrite],
        back_converter: BenchlingConverter,
        bulk_method: Callable[[Iterable[BenchlingWrite]], AsyncTaskLink],
    ) -> Iterable[DataObject | ErrorObject]:
        """
        Calls the given `bulk_method` on the `page` of `DataObject`
        instances.

        If this page fails, it is retried with each element
        individually.
        """

        task = self.__wait_for_task(
            page,
            bulk_method
        )

        if task.status == 'FAILED':
            if len(page) > 1:
                return self.__retry_bulk_methods_on_singletons(
                    object_type,
                    page,
                    back_converter,
                    bulk_method
                )
            else:
                return [
                    ErrorObject(
                        task.errors.to_dict(),
                        object_type,
                        http_code=400
                    )
                ]

        return back_converter.convert_return_entites(
            task.response.additional_properties['customEntities']
        )

    def __retry_bulk_methods_on_singletons(
        self,
        object_type: str,
        page: list[BenchlingWrite],
        back_converter: BenchlingConverter,
        bulk_method: Callable[[Iterable[BenchlingWrite]], AsyncTaskLink],
    ) -> list[DataObject | ErrorObject]:
        """
        Retries a failed page, iterating the bulk method
        on a singleton of each element.
        """

        output_singletons = (
            self.__do_bulk_method_on_page(
                object_type,
                [obj],
                back_converter,
                bulk_method
            )
            for obj in page
        )

        return list(
            chain.from_iterable(output_singletons)
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
            }
            for k1, v1 in self.entities.items()
        }

    @property
    def supported_types(self) -> List:
        return list(self.entities.keys())

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

    def get_page_size(self) -> int:
        return 20

    def __get_one_by_id(
        self,
        object_type: str,
        object_id: str
    ) -> BenchlingReturn:

        try:
            return self.benchling_interface.custom_entities.get_by_id(
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
