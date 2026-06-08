# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Any

from ..datasource_filter import DataSourceFilter
from ..filter_strategy import AttributeMetadataProvider, DateNormalisingPreprocessor


class _DataSourceMetadataAdapter(AttributeMetadataProvider):
    """Adapts a _Filterable DataSource to the AttributeMetadataProvider interface."""

    def __init__(self, datasource: '_Filterable'):
        self._datasource = datasource

    def get_attribute_metadata_by_name(self, object_type, field_name):
        return self._datasource.get_attribute_metadata_by_name(object_type, field_name)


class _Filterable(ABC):
    """
    Implements methods for data sources that support filtering
    e.g. ListGetter, PageGetter and Counter
    """

    def _preprocess_filter(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None = None,
    ) -> DataSourceFilter | None:
        """
        This method is called inside a datasource before starting its associated filter converter.
        This method, unlike the converter, converts in place.
        By default, this method converts relative dates into absolute dates.
        """
        if object_filters is None:
            return None
        preprocessor = DateNormalisingPreprocessor(
            _DataSourceMetadataAdapter(self)
        )
        return preprocessor.preprocess(object_type, object_filters)

    @abstractmethod
    def get_attribute_metadata_by_name(self, obj_type: str, field_name: str) -> Any:
        raise NotImplementedError('Should be implemented by DataSource')
