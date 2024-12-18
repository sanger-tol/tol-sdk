# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Optional

from prefect import get_client
from prefect.client.schemas.filters import (
    DeploymentFilter,
    FlowFilter,
    FlowRunFilter
)
from prefect.settings import (
    PREFECT_API_TLS_INSECURE_SKIP_VERIFY,
    PREFECT_API_URL,
    update_current_profile
)

from .converter import (
    DefaultObjectConverter,
    DefaultPrefectConverter,
    ObjectConverter,
    PrefectConverter
)
from .filter import (
    CLASS_MAP,
    PrefectFilter,
    PrefectFilterBuilder
)
from .prefect_datasource import PrefectDataSource


class _FactoryManager:
    """Manages the converter factory methods"""

    def __init__(self) -> None:
        self.__ds: Optional[PrefectDataSource] = None

    @property
    def data_source(self) -> Optional[PrefectDataSource]:
        return self.__ds

    @data_source.setter
    def data_source(self, prefect_ds: PrefectDataSource) -> None:
        self.__ds = prefect_ds

    def object_converter_factory(self) -> ObjectConverter:
        return DefaultObjectConverter(self.data_source)

    def prefect_converter_factory(self) -> PrefectConverter:
        return DefaultPrefectConverter(self.data_source)


def _filter_factory() -> PrefectFilter:
    builder = PrefectFilterBuilder(
        FlowRunFilter,
        DeploymentFilter,
        FlowFilter,
        CLASS_MAP
    )

    return PrefectFilter(builder)


def _set_config(
    api_url: str,
    insecure: bool
) -> None:

    update_current_profile(
        {
            PREFECT_API_URL: api_url,
        }
    )

    if insecure:
        update_current_profile(
            {
                PREFECT_API_TLS_INSECURE_SKIP_VERIFY: '1'
            }
        )


def create_prefect_datasource(
    api_url: str,
    insecure: bool = False,
) -> PrefectDataSource:
    """Instantiates `PrefectDataSource`."""

    _set_config(api_url, insecure)

    manager = _FactoryManager()

    prefect_ds = PrefectDataSource(
        get_client,
        _filter_factory,
        manager.object_converter_factory,
        manager.prefect_converter_factory
    )

    manager.data_source = prefect_ds

    return prefect_ds
