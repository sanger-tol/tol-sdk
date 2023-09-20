# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Iterable, List, Type

import pytz

from . import DataSource, DataSourceFilter
from .core_converter import DefaultDataObjectToDataObjectConverter


class DataLoader():
    def __init__(self, source: DataSource, destination: DataSource,
                 audit: DataSource, dependencies: List[Type['DataLoader']],
                 source_object_type: str, destination_object_type: str,
                 loader_name: str, convert_class=DefaultDataObjectToDataObjectConverter,
                 object_filters: DataSourceFilter = None):

        self._source = source
        self._destination = destination
        self._audit = audit
        self._dependencies = dependencies
        self._convert_class = convert_class
        self._source_object_type = source_object_type
        self._destination_object_type = destination_object_type
        self._loader_name = loader_name
        self._object_filters = object_filters

    def load(self, field_prefix: str = None):
        self._record_time('start')
        source_objs = self._source.get_list(self._source_object_type,
                                            object_filters=self._object_filters)
        converted_objs = self._convert_objects(source_objs, self._convert_class)
        self._destination.upsert(self._destination_object_type, converted_objs,
                                 field_prefix=field_prefix)
        self._record_time('end')

    def _record_time(self, start_or_end: str):
        new_datetime = datetime.now(pytz.UTC)
        CoreDataObject = self._audit.data_object_factory # noqa N806
        audit_obj = CoreDataObject(
            'data_load_event',
            data={'id': self._loader_name, f'{start_or_end}_time': new_datetime,
                  'source_object_type': self._source_object_type,
                  'destination_object_type': self._destination_object_type}
        )
        self._audit.upsert('data_load_event', [audit_obj])

    def _convert_objects(self, objs: Iterable, _convert_class):
        converted_objects = _convert_class().convert(objs, self._destination)
        return converted_objects
