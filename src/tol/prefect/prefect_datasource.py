# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import asyncio
from typing import Any, Callable, Iterable, Optional, Union
from uuid import UUID

from prefect.client.orchestration import PrefectClient
from prefect.client.schemas.objects import FlowRun
from prefect.client.schemas.sorting import FlowRunSort
from prefect.exceptions import ObjectNotFound

from .converter import ObjectConverter, PrefectConverter
from .filter import PrefectFilter
from .prefect_object import FlowRunObject
from ..core import DataSource, DataSourceError, DataSourceFilter
from ..core.operator import (
    DetailGetter,
    Inserter,
    ListGetter,
    PageGetter
)


class PrefectDataSource(
    DataSource,

    DetailGetter,
    Inserter,
    ListGetter,
    PageGetter
):
    """
    Manages the prefect async infrastructure.

    Most developers will wish to use
    `create_prefect_datasource`, instead of this
    directly.
    """

    def __init__(
        self,
        client_factory: Callable[[], PrefectClient],
        filter_factory: Callable[[], PrefectFilter],
        object_converter_factory: Callable[[], ObjectConverter],
        prefect_converter_factory: Callable[[], PrefectConverter]
    ) -> None:

        self.__client_factory = client_factory
        self.__filter_factory = filter_factory
        self.__oc_factory = object_converter_factory
        self.__prc_factory = prefect_converter_factory

        super().__init__({})

    @property
    def supported_types(self) -> list[str]:
        return ['flow_run']

    @property
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            'flow_run': {
                'flow_name': 'str',
                'deployment_name': 'str',
                'name': 'str',
                'tags': 'list[str]',
                'state': 'str',
                'idempotency_key': 'str',
                'parameters': 'dict[str, Any]'
            }
        }

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[str],
        **kwargs,
    ) -> Iterable[Optional[FlowRunObject]]:

        self.__validate_object_type(object_type)

        return asyncio.run(
            self.__async_get_by_id(object_ids)
        )

    def get_flow_run(self, flow_run_id: str) -> Optional[FlowRunObject]:
        """
        Gets the `FlowRunObject` with the given `flow_run_id`.

        Returns `None` if not found.
        """

        iter_results = self.get_by_id('flow_run', [flow_run_id])
        return iter_results[0]

    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: Optional[int] = None,
        object_filters: Optional[DataSourceFilter] = None,
        sort_by: Optional[str] = None
    ) -> tuple[Iterable[FlowRunObject], None]:
        """
        Gets paged results of `FlowRun` flavoured `DataObject`
        instances.

        Does not return count of results. [BUG]
        """

        if sort_by is not None:
            self.__raise_sort_by_error()

        self.__validate_object_type(object_type)

        size = page_size if page_size else self.get_page_size()

        filter_kwargs = self.__get_filter_kwargs(object_filters)

        return asyncio.run(
            self.__async_get_list_page(page_number, size, filter_kwargs)
        )

    def get_list(
        self,
        object_type: str,
        object_filters: Optional[DataSourceFilter] = None
    ) -> Iterable[FlowRunObject]:

        page = 1

        while True:
            (results_page, _) = self.get_list_page(
                object_type,
                page,
                page_size=self.get_page_size(),
                object_filters=object_filters
            )

            if not results_page:
                return

            yield from results_page
            page += 1

    def insert(
        self,
        object_type: str,
        objects: Iterable[FlowRunObject]
    ) -> Iterable[FlowRunObject]:

        self.__validate_object_type(object_type)

        return asyncio.run(
            self.__async_insert(objects)
        )

    def insert_flow_run_iterable(
        self,
        objects: Iterable[FlowRunObject]
    ) -> Iterable[FlowRunObject]:
        """Inserts `FlowRunObject` instances into the prefect work queue"""

        return self.insert('flow_run', objects)

    def insert_flow_run(self, obj: FlowRunObject) -> FlowRunObject:
        """
        Inserts a single `FlowRunObject` instance into the prefect work queue
        """

        iter_result = self.insert_flow_run_iterable([obj])
        return list(iter_result)[0]

    async def get_names(
        self,
        deployment_id: Union[str, UUID]
    ) -> tuple[str, str]:
        """
        Given a `deployment_id`, returns the names
        of the corresponding flow and deployment.
        """

        async with self.__client_factory() as client:
            deployment = await client.read_deployment(
                deployment_id
            )
            flow_id = deployment.flow_id
            flow = await client.read_flow(flow_id)

        return flow.name, deployment.name

    async def get_deployment_id(
        self,
        flow_name: str,
        deployment_name: str
    ) -> Union[str, UUID]:
        """
        Given a `flow_name` and `deployment_name`, returns
        the UUID of the latter deployment.
        """

        name = f'{flow_name}/{deployment_name}'

        async with self.__client_factory() as client:
            deployment = await client.read_deployment_by_name(name)
            return deployment.id

    def __validate_object_type(self, object_type: str) -> None:
        if object_type != 'flow_run':
            self.__raise_bad_type_error()

    async def __async_get_by_id(
        self,
        object_ids: Iterable[str]
    ) -> Iterable[Optional[FlowRunObject]]:

        async with self.__client_factory() as client:
            fetched = [
                await self.__read_flow_run(client, id_)
                for id_ in object_ids
            ]

        return await self.__prc_factory().async_convert_iterable(fetched)

    async def __read_flow_run(
        self,
        client: PrefectClient,
        flow_run_id: Union[str, UUID]
    ) -> Optional[FlowRun]:

        try:
            return await client.read_flow_run(flow_run_id)
        except ObjectNotFound:
            return None

    async def __async_get_list_page(
        self,
        page_number: int,
        page_size: int,
        filter_kwargs: dict[str, Any]
    ) -> tuple[Iterable[FlowRunObject], None]:

        flow_runs = await self.__read_flow_runs(page_number, page_size, filter_kwargs)

        return await self.__prc_factory().async_convert_iterable(flow_runs), None

    async def __read_flow_runs(
        self,
        page_number: int,
        page_size: int,
        filter_kwargs: dict[str, Any]
    ) -> Iterable[FlowRun]:

        async with self.__client_factory() as client:
            return await client.read_flow_runs(
                sort=FlowRunSort.ID_DESC,
                limit=page_size,
                offset=(page_number - 1) * page_size,
                **filter_kwargs
            )

    def __get_filter_kwargs(
        self,
        object_filters: Optional[DataSourceFilter]
    ) -> dict[str, Any]:

        if object_filters is None:
            return {}

        return self.__filter_factory().to_kwargs(object_filters)

    async def __insert_kwargs_iterable(
        self,
        kwargs_iterable: Iterable[dict[str, Any]]
    ) -> Iterable[FlowRun]:

        async with self.__client_factory() as client:
            return [
                await self.__insert_kwargs(client, kwargs)
                for kwargs in kwargs_iterable
            ]

    async def __insert_kwargs(
        self,
        client: PrefectClient,
        kwargs: dict[str, Any]
    ) -> FlowRun:

        return await client.create_flow_run_from_deployment(
            **kwargs
        )

    async def __async_insert(
        self,
        objects: Iterable[FlowRunObject]
    ) -> Iterable[FlowRunObject]:

        kwargs_iter = await self.__oc_factory().async_convert_iterable(
            objects
        )
        flow_runs = await self.__insert_kwargs_iterable(kwargs_iter)
        return await self.__prc_factory().async_convert_iterable(
            flow_runs
        )

    def __raise_sort_by_error(self) -> None:
        raise DataSourceError(
            title='Sort Unsupported',
            detail='Sorting is unsupported on `PrefectDataSource`',
            status_code=400
        )

    def __raise_bad_type_error(self) -> None:
        raise DataSourceError(
            title='Bad Object Type',
            detail='Only "flow_run" is supported on `PrefectDataSource`.',
            status_code=400
        )
