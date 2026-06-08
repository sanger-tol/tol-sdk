# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from .datasource_filter import DataSourceFilter

T = TypeVar('T')  # The target query type (str, dict, Select)


class FilterStrategy(ABC, Generic[T]):
    """
    Strategy interface for converting a DataSourceFilter into
    a source-specific query representation.
    """

    @abstractmethod
    def convert(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None = None
    ) -> T | None:
        """Convert a DataSourceFilter to the target query format."""


class FilterPreprocessor(ABC):
    """
    A single preprocessing step applied to a DataSourceFilter
    before conversion.
    """

    @abstractmethod
    def preprocess(
        self,
        object_type: str,
        object_filters: DataSourceFilter
    ) -> DataSourceFilter:
        """Transform the filter in place and return it."""


class AttributeMetadataProvider(ABC):
    """Extracts attribute metadata lookup from DataSource coupling."""

    @abstractmethod
    def get_attribute_metadata_by_name(
        self, object_type: str, field_name: str
    ) -> dict[str, Any] | None:
        pass


class DateNormalisingPreprocessor(FilterPreprocessor):
    """
    Converts relative date strings (e.g. '2 days ago') to absolute
    datetime objects using attribute metadata.
    """

    def __init__(self, metadata_provider: AttributeMetadataProvider):
        self._metadata = metadata_provider

    def preprocess(self, object_type, object_filters):
        if object_filters.and_ is None:
            return object_filters
        for name, value in object_filters.and_.items():
            metadata = self._metadata.get_attribute_metadata_by_name(object_type, name)
            if metadata is None:
                continue
            for op, val in value.items():
                if 'value' in val and metadata['python_type'] == 'datetime' \
                        and isinstance(val['value'], str):
                    import dateparser
                    object_filters.and_[name][op]['value'] = dateparser.parse(val['value'])
        return object_filters


class CompositeFilterStrategy(FilterStrategy[T]):
    """
    Composes a pipeline of preprocessors with a final conversion strategy.
    Decorator pattern applied to FilterStrategy.
    """

    def __init__(
        self,
        delegate: FilterStrategy[T],
        preprocessors: list[FilterPreprocessor] | None = None,
    ):
        self._delegate = delegate
        self._preprocessors = preprocessors or []

    def convert(self, object_type, object_filters=None):
        if object_filters is not None:
            for preprocessor in self._preprocessors:
                object_filters = preprocessor.preprocess(object_type, object_filters)
        return self._delegate.convert(object_type, object_filters)
