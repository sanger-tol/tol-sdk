# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable, List

from ..utils.config import CombinedConfig, IndividualConfig
from ...core import (
    DataId,
    DataObject,
    DataSource,
    DataSourceFilter
)


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

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
        **kwargs
    ) -> List[DataObject]:
        pass

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
        individual_config: IndividualConfig = self.combined[object_type]
        print(individual_config)
        return operation_name in individual_config.data_source.supported_operations
