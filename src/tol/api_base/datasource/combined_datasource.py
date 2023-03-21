# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Iterable, List

from ..utils.config import CombinedConfig, IndividualConfig
from ...core import (
    DataId,
    DataObject,
    DataSource,
    DataSourceFilter
)


class UnsupportedOperationForTypeError(NotImplementedError):
    def __init__(
        self,
        object_type: str,
        operation_name: str,
    ):
        super().__init__(
            f'The operation {operation_name} is unsupported '
            f'for the type {object_type}.'
        )


def delegate(operation: Callable) -> Callable:
    operation_name = operation.__name__

    @wraps(operation)
    def wrapper(
        combined_ds: CombinedDataSource,
        object_type: str,
        *args,
        **kwargs
    ) -> Any:
        if not combined_ds.operation_is_supported_for_type(
            object_type,
            operation_name
        ):
            raise UnsupportedOperationForTypeError(
                object_type,
                operation_name
            )
        return combined_ds.delegate_operation(
            object_type,
            operation_name,
            *args,
            **kwargs
        )
    return wrapper


class CombinedDataSource(DataSource):
    """
    The nested DataSource that combines all
    other DataSource instances
    """

    def __init__(self, combined_config: CombinedConfig):
        datasource_config = {
            'combined': combined_config
        }
        super().__init__(datasource_config)

    @delegate
    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
        **kwargs
    ) -> List[DataObject]:
        pass

    @delegate
    def get_list_page(
        self,
        object_type: str,
        page_number: int,
        page_size: int = None,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> List[DataObject]:
        pass

    def operation_is_supported_for_type(
        self,
        object_type: str,
        operation_name: str
    ) -> bool:
        data_source = self.__get_data_source_for_type(object_type)
        return operation_name in data_source.supported_operations

    def delegate_operation(
        self,
        object_type: str,
        operation_name: str,
        *args,
        **kwargs
    ) -> Any:
        subordinate_ds = self.__get_data_source_for_type(object_type)
        subordinate_op = getattr(subordinate_ds, operation_name)
        return subordinate_op(
            object_type,
            *args,
            **kwargs
        )

    def __get_data_source_for_type(self, object_type: str) -> DataSource:
        individual_config: IndividualConfig = self.combined[object_type]
        return individual_config.data_source
