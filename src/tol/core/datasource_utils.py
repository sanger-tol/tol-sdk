# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
from typing import Iterator

from .data_object import DataObject
from .datasource import DataSource
from .datasource_error import DataSourceError
from .datasource_filter import DataSourceFilter


class DataSourceUtils:

    @classmethod
    def get_datasource_by_name(
        cls,
        name: str,
        environment: str
    ) -> DataSource:
        module = importlib.import_module(f'tol.sources.{name}')
        class_ = getattr(module, name)
        return class_(environment=environment)

    @classmethod
    def get_ids(
        cls,
        datasource: DataSource,
        object_type: str,
        id_attribute: str,
        object_filters: DataSourceFilter = None
    ) -> Iterator[str]:
        try:
            yield from cls.__get_ids_via_group_stats(
                datasource,
                object_type,
                id_attribute,
                object_filters
            )
        except (DataSourceError, AttributeError):
            # If the datasource does not support group stats, we will
            # fall back to get_list
            yield from cls.__get_ids_via_get_list(
                datasource,
                object_type,
                id_attribute,
                object_filters
            )

    @classmethod
    def __get_ids_via_group_stats(
        cls,
        datasource: DataSource,
        object_type: str,
        id_attribute: str,
        object_filters: DataSourceFilter = None
    ) -> Iterator[str]:
        uniques = datasource.get_group_stats(
            object_type,
            group_by=[id_attribute],
            stats_fields=[],
            stats=[],
            object_filters=object_filters
        )
        for unique in uniques:
            yield unique['key'][id_attribute]

    @classmethod
    def __get_ids_via_get_list(
        cls,
        datasource: DataSource,
        object_type: str,
        id_attribute: str,
        object_filters: DataSourceFilter = None
    ) -> Iterator[str]:
        ids_seen = set()
        objs = datasource.get_list(
            object_type,
            object_filters=object_filters
        )
        for obj in objs:
            id_ = obj.get_field_by_name(id_attribute)
            if id_ not in ids_seen:
                ids_seen.add(id_)
                yield str(id_)  # May need to revisit this string conversion

    @classmethod
    def get_objects_from_ids(
        cls,
        datasource: DataSource,
        object_type: str,
        ids: Iterator[str],
        sort_by: str = None,
    ) -> Iterator[DataObject]:
        objs = datasource.get_by_ids(object_type, ids)
        if sort_by is not None:
            yield from sorted(objs, key=lambda obj: obj.get_field_by_name(sort_by) or 0)
        else:
            yield from objs
