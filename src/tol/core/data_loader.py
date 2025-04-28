# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from itertools import chain, groupby
from typing import Dict, Iterable, List, Optional, Type

from more_itertools import peekable

from tol.core import is_iter

from .core_converter import Converter
from .data_object import DataObject
from .data_object_converter import DataObjectToDataObjectOrUpdateConverter
from .datasource import DataSource
from .datasource_filter import DataSourceFilter


class DataLoader(ABC):
    @abstractmethod
    def load(self, field_prefix: str = None, dry_run: bool = False, **kwargs):
        """
        Loads a set of object from one DataSource to another
        """


class DefaultDataLoader():
    def __init__(
        self,
        source: DataSource,
        destination: DataSource,
        dependencies: List[Type['DataLoader']],
        source_object_type: str,
        loader_name: str,
        destination_object_type: str = '',
        audit: Optional[DataSource] = None,
        convert_class: Optional[DataObjectToDataObjectOrUpdateConverter] = None,
        object_filters: Optional[DataSourceFilter] = None,
        converter: Converter | None = None
    ):
        self._source = source
        self._destination = destination
        self._audit = audit
        self._dependencies = dependencies
        self._converter = self.__get_converter(convert_class, converter)
        self._converter.data_loader = self  # Set here to avoid circular import
        self._source_object_type = source_object_type
        self._destination_object_type = destination_object_type
        self._loader_name = loader_name
        self._object_filters = object_filters

    def load(
        self,
        field_prefix: str = None,
        dry_run: bool = False,
        candidate_key: Optional[List[str]] = ['id'],
        method: str = 'upsert',
        auto_exhaust: bool = True
    ):
        if not dry_run:
            self._record_time('start')

        source_objs = self._get_source_objects()
        converted_objs = self._convert_objects(source_objs, self._converter)

        if '' == self._destination_object_type:
            returned_objects = self._process_data_loads(
                candidate_key=candidate_key,
                converted_objs=converted_objs,
                dry_run=dry_run,
                field_prefix=field_prefix,
                method=method
            )
        else:
            returned_objects = self._process_data_load(
                candidate_key=candidate_key,
                converted_objs=converted_objs,
                dry_run=dry_run,
                field_prefix=field_prefix,
                method=method,
                destination_object_type=self._destination_object_type
            )

        if not dry_run:
            self._record_time('end')
            converter_return_object = self._check_converter_for_returned_objects()
            if is_iter(converter_return_object) and is_iter(returned_objects):
                returned_objects = chain(
                    returned_objects,
                    converter_return_object
                )

            if is_iter(returned_objects) and auto_exhaust:
                # Exhaust the returned objects
                for _ in returned_objects:
                    pass

            return returned_objects

    def _process_data_loads(
        self,
        converted_objs: Iterable[object],
        candidate_key: List[str] = ['id'],
        dry_run: bool = False,
        field_prefix: str = None,
        method: str = 'upsert'
    ):
        grouped_sorted_converted_objects = self._get_sorted_converted_objs(converted_objs)
        all_returned_objects = iter([])

        for key in grouped_sorted_converted_objects.keys():
            returned_objects = self._process_data_load(
                candidate_key=candidate_key,
                converted_objs=grouped_sorted_converted_objects[key],
                dry_run=dry_run,
                field_prefix=field_prefix,
                method=method,
                destination_object_type=key
            )

            all_returned_objects = chain(all_returned_objects, returned_objects)

        return all_returned_objects

    def _get_sorted_converted_objs(
            self,
            converted_objs: Iterable[object]
    ) -> Dict[str, Iterable[object]]:
        sorted_objects = sorted(converted_objs, key=lambda obj: obj.type)

        return {
            key: list(group) for key, group in groupby(sorted_objects, key=lambda obj: obj.type)
        }

    def _process_data_load(
        self,
        destination_object_type: str,
        converted_objs: Iterable[object],
        candidate_key: List[str] = ['id'],
        dry_run: bool = False,
        field_prefix: str = None,
        method: str = 'upsert'
    ):
        returned_objects = []
        if candidate_key == ['id']:
            if not dry_run:
                insert_method = getattr(self._destination, method)
                returned_objects = insert_method(
                    destination_object_type,
                    objects=converted_objs,
                    field_prefix=field_prefix
                )
            else:
                for converted_obj in converted_objs:
                    print(f'{converted_obj.id}: {converted_obj.attributes}')
        else:
            if not dry_run:
                returned_objects = self._destination.update(
                    object_type=destination_object_type,
                    updates=converted_objs,
                    candidate_key=candidate_key,
                    field_prefix=field_prefix
                )
            else:
                for converted_obj_id, converted_obj in converted_objs:
                    print(converted_obj_id, converted_obj)

        return returned_objects

    def __get_converter(
        self,
        convert_class: type[Converter] | None,
        converter: Converter | None
    ) -> Converter:

        if converter is not None:
            return converter

        if convert_class is not None:
            return convert_class(
                data_object_factory=self._destination.data_object_factory
            )

        raise Exception(
            'Either `convert_class` or `converter` must be specified.'
        )

    def _get_source_objects(self) -> Iterable:
        source_objs = self._source.get_list(
            self._source_object_type,
            object_filters=self._object_filters)
        return source_objs

    def _record_time(self, start_or_end: str):
        if self._audit is None:
            return
        new_datetime = datetime.now(timezone.utc)
        CoreDataObject = self._audit.data_object_factory  # noqa N806

        destination_object_type = 'multiple' \
            if self._destination_object_type == '' else self._destination_object_type

        audit_obj = CoreDataObject(
            'data_load_event',
            id_=self._loader_name,
            attributes={
                f'{start_or_end}_time': new_datetime,
                'source_object_type': self._source_object_type,
                'destination_object_type': destination_object_type
            }
        )
        self._audit.upsert('data_load_event', [audit_obj])

    def _convert_objects(self, objs: Iterable, _converter):
        converted_objects = _converter.convert_iterable(objs)

        return converted_objects

    def _check_converter_for_returned_objects(self):
        return_objects = self._converter.get_return_objects()

        if not 0 == len(return_objects):
            for return_object in return_objects:
                return_object.attributes['retrieved'] = True

            return iter(return_objects)

        return None


class GroupStatterDataLoader(DefaultDataLoader):

    def get_default_converter(self):
        # This will convert:
        # [{'key': {'field1': 'ID123', 'subfield': 'CAT'}
        #   'stats': {'count': 123, 'other': {'stat': 345}}},
        #  {'key': {'field1': 'ID123', 'subfield': 'DOG'}
        #   'stats': {'count': 456, 'other': {'stat': 678}}}
        # ]
        # to a CoreDataObject of type destination_object_type
        # with id: ID123
        # and attributes {'count_cat': 123,
        #                 'count_dog': 456,
        #                 'other_stat_cat': 345,
        #                 'other_stat_dog': 678}}
        data_loader = self

        class DefaultGroupStatToDataObjectConverter(DataObjectToDataObjectOrUpdateConverter):
            def convert_iterable(
                self,
                inputs: Iterable[DataObject]
            ) -> Iterable[DataObject]:
                peekable_inputs = peekable(inputs)
                additional_attributes = {}
                for input_ in peekable_inputs:
                    data_object = next(self.convert(input_))  # There will be one
                    # We might have some attributes here from before
                    for attr_name, attr_value in additional_attributes.items():
                        setattr(data_object, attr_name, attr_value)
                    next_stat = peekable_inputs.peek(None)
                    if next_stat is not None and \
                            next_stat['key'][data_loader._group_statter_group_by[0]] \
                            == data_object.id:
                        # We have more stats coming for this ID
                        additional_attributes = data_object.attributes
                    else:
                        additional_attributes = {}
                        yield data_object

            def convert(self, data_object: DataObject) -> Iterable[DataObject]:
                # It's not a DataObject, sorry!
                CoreDataObject = self._data_object_factory  # noqa N806
                source_object_type = data_loader._source_object_type
                # This gets the string to append
                append_string = '_'.join(data_object['key'][k]
                                         for k in data_loader._group_statter_group_by[1::])
                append_string = append_string.lower()
                if append_string != '':
                    append_string = f'{append_string}_'
                attributes = {}
                attributes[f'{source_object_type}_{append_string}count'] \
                    = data_object['stats']['count']
                for stats_field in data_loader._group_statter_stats_fields:
                    for stat in data_loader._group_statter_stats:
                        attributes[f'{source_object_type}_{stats_field}_{append_string}{stat}'] = \
                            data_object['stats'][stats_field][stat]
                ret1 = CoreDataObject(
                    id_=data_object['key'][data_loader._group_statter_group_by[0]],
                    type_=data_loader._destination_object_type,
                    attributes=attributes
                )
                yield ret1
        return DefaultGroupStatToDataObjectConverter

    def __init__(
        self,
        source: DataSource,
        destination: DataSource,
        dependencies: List[Type['DataLoader']],
        source_object_type: str, destination_object_type: str,
        loader_name: str,
        audit: DataSource = None,
        convert_class: Optional[DataObjectToDataObjectOrUpdateConverter] = None,
        object_filters: Optional[DataSourceFilter] = None,
        group_statter_group_by: Optional[str] = None,
        group_statter_stats_fields: Optional[List[str]] = [],
        group_statter_stats: Optional[List[str]] = ['min', 'max']
    ):
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
        source_objs = self._source.get_group_stats(
            self._source_object_type,
            group_by=self._group_statter_group_by,
            stats_fields=self._group_statter_stats_fields,
            stats=self._group_statter_stats,
            object_filters=self._object_filters,
        )
        return source_objs


class IdsDataLoader(DefaultDataLoader):
    def __init__(self, source: DataSource, destination: DataSource,
                 dependencies: List[Type['DataLoader']],
                 source_object_type: str, destination_object_type: str,
                 loader_name: str,
                 audit: Optional[DataSource] = None,
                 convert_class: Optional[DataObjectToDataObjectOrUpdateConverter] = None,
                 object_ids: Optional[Iterable[str]] = None,
                 converter: Converter | None = None):
        super().__init__(
            source=source, destination=destination,
            dependencies=dependencies, source_object_type=source_object_type,
            destination_object_type=destination_object_type,
            loader_name=loader_name, audit=audit,
            converter=converter,
            convert_class=convert_class)
        self._object_ids = object_ids

    def _get_source_objects(self) -> Iterable:
        source_objs = self._source.get_by_ids(
            self._source_object_type,
            self._object_ids)
        return source_objs


class ObjectsDataLoader(DefaultDataLoader):
    def __init__(self, source: DataSource, destination: DataSource,
                 dependencies: List[Type['DataLoader']],
                 source_object_type: str, destination_object_type: str,
                 loader_name: str,
                 audit: Optional[DataSource] = None,
                 convert_class: Optional[DataObjectToDataObjectOrUpdateConverter] = None,
                 objects: Optional[Iterable[DataObject]] = None):
        super().__init__(
            source=source, destination=destination,
            dependencies=dependencies, source_object_type=source_object_type,
            destination_object_type=destination_object_type,
            loader_name=loader_name, audit=audit,
            convert_class=convert_class)
        self._objects = objects

    def _get_source_objects(self) -> Iterable:
        return self._objects
