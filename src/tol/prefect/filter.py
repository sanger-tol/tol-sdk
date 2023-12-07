# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Callable, Optional, Union

from prefect.client.schemas.filters import (
    DeploymentFilter,
    DeploymentFilterName,
    FlowFilter,
    FlowFilterName,
    FlowRunFilter,
    FlowRunFilterId,
    FlowRunFilterIdempotencyKey,
    FlowRunFilterName,
    FlowRunFilterState,
    FlowRunFilterTags
)

from ..core import DataSourceError, DataSourceFilter


CLASS_MAP = {
    'id': FlowRunFilterId,
    'idempotency_key': FlowRunFilterIdempotencyKey,
    'name': FlowRunFilterName,
    'state': FlowRunFilterState,
    'tags': FlowRunFilterTags,
    'flow_name': FlowFilterName,
    'deployment_name': DeploymentFilterName
}


_PrefectFilter = Union[
    DeploymentFilter,
    FlowFilter,
    FlowRunFilter,
]


_FilterKwargsDict = dict[str, Optional[_PrefectFilter]]


class PrefectFilterBuilder:
    """
    Provides a collection of "setter" methods, to add
    filter terms. Returns a `dict` of kwargs, using which
    to instantiate `FlowRunFilter`.
    """

    def __init__(
        self,
        flow_run_class: type[FlowRunFilter],
        deployment_class: type[DeploymentFilter],
        flow_class: type[FlowFilter],
        class_map: dict[str, type]
    ) -> None:

        self.__filters: _FilterKwargsDict = {}

        self.__flow_run_class = flow_run_class
        self.__deployment_class = deployment_class
        self.__flow_class = flow_class

        self.__class_map = class_map

    @property
    def kwargs(self) -> _FilterKwargsDict:
        return {
            'flow_run_filter': self.__flow_run_filter,
            'deployment_filter': self.__deployment_filter,
            'flow_filter': self.__flow_filter
        }

    def id_(self, any_: list[str]) -> None:
        self.__set_any('id', any_)

    def flow_name(self, any_: list[str]) -> None:
        self.__set_any('_flow_name', any_)

    def deployment_name(self, any_: list[str]) -> None:
        self.__set_any('_deployment_name', any_)

    def idempotency_key(self, any_: list[str]) -> None:
        self.__set_any('idempotency_key', any_)

    def name(self, any_: list[str]) -> None:
        self.__set_any('name', any_)

    def state(self, any_: list[str]) -> None:
        self.__set_any('state', any_)

    def tags_all(self, all_: list[str]) -> None:
        """
        Note - all tags must be present in this filter.

        Not just any individual one.
        """
        self.__set_all('tags', all_)

    @property
    def __flow_run_filter(self) -> Optional[FlowRunFilter]:
        kwargs = {
            k: v
            for k, v in self.__filters.items()
            if not k.startswith('_')
        }
        if not kwargs:
            return None
        return self.__flow_run_class(**kwargs)

    @property
    def __deployment_filter(self) -> Optional[DeploymentFilter]:
        kwargs = self.__pull_out_filters('_deployment_')
        if not kwargs:
            return None
        return self.__deployment_class(**kwargs)

    @property
    def __flow_filter(self) -> Optional[FlowFilter]:
        kwargs = self.__pull_out_filters('_flow_')
        if not kwargs:
            return None
        return self.__flow_class(**kwargs)

    def __pull_out_filters(
        self,
        initial: str
    ) -> Optional[_FilterKwargsDict]:

        start = len(initial)

        return {
            k[start:]: v
            for k, v in self.__filters.items()
            if k.startswith(initial)
        }

    def __set_any(
        self,
        name: str,
        any_: list[str]
    ) -> None:

        self.__set(name, any_=any_)

    def __set_all(
        self,
        name: str,
        all_: list[str]
    ) -> None:

        self.__set(name, all_=all_)

    def __set(self, name: str, **kwargs) -> None:
        stripped = name.lstrip('_')
        class_ = self.__class_map[stripped]
        self.__filters[name] = class_(**kwargs)


class PrefectFilter:
    """
    Converts a `DataSourceFilter` instance to a form
    that `PrefectDataSource` can understand.
    """

    __VALID_KEYS = (
        'id',
        'idempotency_key',
        'name',
        'state',
        'tags',
        'flow_name',
        'deployment_name'
    )

    def __init__(
        self,
        builder: PrefectFilterBuilder
    ) -> None:

        self.__builder = builder

    def to_kwargs(
        self,
        filters: DataSourceFilter
    ) -> _FilterKwargsDict:
        """Returns filter kwargs to add to get operations"""

        self.__validate_filter_roots(filters)

        self.__add_all_exact(filters)
        self.__add_all_in_list(filters)

        return self.__builder.kwargs

    def __add_all_exact(
        self,
        filters: DataSourceFilter
    ) -> None:

        if not filters.exact:
            return

        for k, v in filters.exact.items():
            self.__add_exact(k, v)

    def __add_all_in_list(
        self,
        filters: DataSourceFilter
    ) -> None:

        if not filters.in_list:
            return

        for k, v in filters.in_list.items():
            self.__add_in_list(k, v)

    def __add_exact(self, k: str, v: Any) -> None:
        self.__check_valid_key(k)

        if k == 'tags':
            return self.__add_exact_tags(v)

        if isinstance(v, list):
            self.__raise_bad_list_exact(k)

        self.__get_builder_method(k)([v])

    def __add_in_list(self, k: str, v: list[str]) -> None:
        self.__check_valid_key(k)

        if k == 'tags':
            self.__in_list_error_tags()

        self.__get_builder_method(k)(v)

    def __add_exact_tags(
        self,
        v: Union[str, list[str]]
    ) -> None:

        if isinstance(v, str):
            return self.__builder.tags_all([v])

        self.__builder.tags_all(v)

    def __in_list_error_tags(self) -> None:
        raise DataSourceError(
            title='Bad Filter',
            detail='Cannot use `in_list` against tags',
            status_code=400
        )

    def __raise_bad_list_exact(self, k: str) -> None:
        raise DataSourceError(
            title='Bad Filter',
            detail=f'Cannot provide a list to exact on {k}.',
            status_code=400
        )

    def __validate_filter_roots(
        self,
        filters: DataSourceFilter
    ) -> None:

        if filters.contains or filters.range:
            raise DataSourceError(
                title='Bad Filter',
                detail='Can only use `exact` and `in_list` terms',
                status_code=400
            )

    def __check_valid_key(self, k: str) -> None:
        if k not in self.__VALID_KEYS:
            raise DataSourceError(
                title='Bad Filter',
                detail='Unknown filter key',
                status_code=400
            )

    def __get_builder_method(
        self,
        k: str
    ) -> Callable:

        if k == 'id':
            return self.__builder.id_

        return getattr(self.__builder, k)
