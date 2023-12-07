# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from typing import Any, Union
from uuid import UUID

from prefect.client.schemas.objects import FlowRun

from .prefect_object import FlowRunObject
from ..core import DataSourceError
from ..core.core_converter import AsyncConverter

if typing.TYPE_CHECKING:
    from .prefect_datasource import PrefectDataSource


PrefectConverter = AsyncConverter[FlowRun, FlowRunObject]
"""
Converts from Prefect-native `FlowRun` to
`DataObject` instances.
"""
ObjectConverter = AsyncConverter[FlowRunObject, dict[str, Any]]
"""
Converts from `DataObject` to a "kwargs" `dict` for
`PrefectClient().create_flow_run_from_deployment()`
"""


class DefaultPrefectConverter(PrefectConverter):
    def __init__(
        self,
        prefect_ds: PrefectDataSource
    ) -> None:

        self.__prefect_ds = prefect_ds
        self.__names_cache: dict[str, tuple[str, str]] = {}

    async def async_convert(self, input_: FlowRun) -> FlowRunObject:
        attributes = await self.__get_attributes(input_)

        return self.__new_object(
            str(input_.id),
            attributes=attributes
        )

    async def __get_names(
        self,
        deployment_id: Union[str, UUID]
    ) -> tuple[str, str]:

        if deployment_id in self.__names_cache:
            return self.__names_cache[deployment_id]

        names = await self.__prefect_ds.get_names(
            deployment_id
        )
        self.__names_cache[deployment_id] = names
        return names

    async def __get_attributes(
        self,
        flow_run: FlowRun
    ) -> dict[str, Any]:

        dep_id = flow_run.deployment_id

        flow_name, deployment_name = await self.__get_names(dep_id)

        return {
            'name': flow_run.name,
            'flow_name': flow_name,
            'deployment_name': deployment_name,
            'state': flow_run.state_name,
            'tags': flow_run.tags,
            'idempotency_key': flow_run.idempotency_key,
            'parameters': flow_run.parameters
        }

    def __new_object(
        self,
        id_: str,
        attributes: dict[str, Any]
    ) -> FlowRunObject:

        return self.__prefect_ds.data_object_factory(
            'flow_run',
            id_,
            attributes=attributes
        )


class DefaultObjectConverter(ObjectConverter):

    __KEYS = (
        'parameters',
        'name',
        'tags',
        'idempotency_key'
    )

    def __init__(self, prefect_ds: PrefectDataSource) -> None:
        self.__ds = prefect_ds
        self.__dep_id_cache: dict[tuple[str, str], str] = {}

    async def async_convert(self, input_: FlowRunObject) -> dict[str, Any]:
        flow_name = input_.attributes.get('flow_name')
        dep_name = input_.attributes.get('deployment_name')

        self.__validate_names(flow_name, dep_name)

        deployment_id = await self.__get_deployment_id(flow_name, dep_name)

        return self.__to_kwargs(deployment_id, input_)

    def __validate_names(self, flow_name: str, dep_name: str) -> None:
        if not flow_name or not dep_name:
            detail = 'A name for both the flow and deployment are required'
            raise DataSourceError(
                title='Name Required',
                detail=detail,
                status_code=400
            )

    async def __get_deployment_id(
        self,
        flow_name: str,
        deployment_name: str
    ) -> Union[str, UUID]:

        __k = (flow_name, deployment_name)

        if __k in self.__dep_id_cache:
            return self.__dep_id_cache[__k]

        __v = await self.__ds.get_deployment_id(
            flow_name,
            deployment_name
        )
        self.__dep_id_cache[__k] = __v
        return __v

    def __to_kwargs(
        self,
        deployment_id: Union[str, UUID],
        obj: FlowRunObject
    ) -> dict[str, Any]:

        attributes = self.__get_relevant_attributes(obj)

        return {
            **attributes,
            'deployment_id': deployment_id
        }

    def __get_relevant_attributes(
        self,
        obj: FlowRunObject
    ) -> dict[str, Any]:

        return {
            k: obj.attributes.get(k)
            for k in self.__KEYS
        }
