# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable, List, Type

import pytz

from .data_object import DataObject
from .data_object_converter import DataObjectToDataObjectConverter
from .datasource import DataSource
from .datasource_filter import DataSourceFilter


class DataLoader(ABC):
    @abstractmethod
    def load(self, field_prefix: str = None, dry_run: bool = False):
        """
        Loads a set of object from one DataSource to another
        """


class DefaultDataLoader():
    def __init__(self, source: DataSource, destination: DataSource,
                 dependencies: List[Type['DataLoader']],
                 source_object_type: str, destination_object_type: str,
                 loader_name: str,
                 audit: DataSource = None,
                 convert_class: DataObjectToDataObjectConverter = None,
                 object_filters: DataSourceFilter = None):

        self._source = source
        self._destination = destination
        self._audit = audit
        self._dependencies = dependencies
        self._converter = convert_class(
            data_object_factory=destination.data_object_factory
        )
        self._source_object_type = source_object_type
        self._destination_object_type = destination_object_type
        self._loader_name = loader_name
        self._object_filters = object_filters

    def load(self, field_prefix: str = None, dry_run: bool = False):
        if not dry_run:
            self._record_time('start')

        source_objs = self._get_source_objects()
        converted_objs = self._convert_objects(source_objs, self._converter)
        if not dry_run:
            self._destination.upsert(self._destination_object_type, converted_objs,
                                     field_prefix=field_prefix)
            self._record_time('end')
        else:
            for converted_obj in converted_objs:
                print(f'{converted_obj.id}: {converted_obj.attributes}')

    def _get_source_objects(self) -> Iterable:
        source_objs = self._source.get_list(
            self._source_object_type,
            object_filters=self._object_filters)
        return source_objs

    def _record_time(self, start_or_end: str):
        if self._audit is None:
            return
        new_datetime = datetime.now(pytz.UTC)
        CoreDataObject = self._audit.data_object_factory  # noqa N806
        audit_obj = CoreDataObject(
            'data_load_event',
            id_=self._loader_name,
            attributes={f'{start_or_end}_time': new_datetime,
                        'source_object_type': self._source_object_type,
                        'destination_object_type': self._destination_object_type}
        )
        self._audit.upsert('data_load_event', [audit_obj])

    def _convert_objects(self, objs: Iterable, _converter):
        converted_objects = _converter.convert_iterable(objs)
        return converted_objects


class GroupStatterDataLoader(DefaultDataLoader):

    def get_default_converter(self):
        # This will convert:
        # {'ID123': 17}
        # to a CoreDataObject of type destination_object_type
        # with id: ID123
        # and attribute source_object_type_count: 17
        data_loader = self

        class DefaultGroupStatToDataObjectConverter(DataObjectToDataObjectConverter):
            def convert(self, data_object: DataObject) -> Iterable[DataObject]:
                CoreDataObject = self._data_object_factory  # noqa N806
                # expecting: {'id123': {'count': count}}
                for k, v in data_object.items():
                    source_object_type = data_loader._source_object_type
                    attributes = {f'{source_object_type}_count': v['count']}
                    for stats_field in data_loader._group_statter_stats_fields:
                        for stat in data_loader._group_statter_stats:
                            attributes[f'{source_object_type}_{stats_field}_{stat}'] = \
                                v[f'{stats_field}_{stat}']
                    ret1 = CoreDataObject(
                        id_=k,
                        type_=data_loader._destination_object_type,
                        attributes=attributes
                    )
                return iter([ret1])
        return DefaultGroupStatToDataObjectConverter

    def __init__(self, source: DataSource, destination: DataSource,
                 dependencies: List[Type['DataLoader']],
                 source_object_type: str, destination_object_type: str,
                 loader_name: str,
                 audit: DataSource = None,
                 convert_class: DataObjectToDataObjectConverter = None,
                 object_filters: DataSourceFilter = None,
                 group_statter_group_by: str = None,
                 group_statter_stats_fields: List[str] = [],
                 group_statter_stats: List[str] = ['min', 'max']):
        if convert_class is None:
            convert_class = self.get_default_converter()
        super().__init__(
            source=source, destination=destination,
            dependencies=dependencies, source_object_type=source_object_type,
            destination_object_type=destination_object_type,
            loader_name=loader_name, audit=audit,
            convert_class=convert_class,
            object_filters=object_filters)
        self._group_statter_group_by = group_statter_group_by
        self._group_statter_stats_fields = group_statter_stats_fields
        self._group_statter_stats = group_statter_stats

    def _get_source_objects(self) -> Iterable:
        source_objs = self._source.get_stats(
            self._source_object_type,
            group_by=self._group_statter_group_by,
            stats_fields=self._group_statter_stats_fields,
            stats=self._group_statter_stats,
            object_filters=self._object_filters)
        return source_objs
