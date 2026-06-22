# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
from typing import Iterable, Iterator

from dacite import from_dict

from .data_object import DataObject
from .data_source_attribute_metadata import data_source_attribute_metadata
from .datasource import DataSource
from .datasource_error import DataSourceError
from .datasource_filter import DataSourceFilter
from .relationship import RelationshipConfig


class DataSourceUtils:

    @classmethod
    def get_datasource(
        cls,
        datasource_instance_id: str,
        config_datasource: DataSource
    ) -> DataSource:
        datasource_instance = config_datasource.get_one(
            'data_source_instance',
            datasource_instance_id
        )
        if datasource_instance is None:
            raise DataSourceError(
                f'Datasource instance with id {datasource_instance_id} not found'
            )
        return cls.get_datasource_by_datasource_instance(datasource_instance)

    @classmethod
    def get_datasource_by_name(
        cls,
        name: str,
        **kwargs
    ) -> DataSource:
        module = importlib.import_module(f'tol.sources.{name}')
        class_ = getattr(module, name)
        return class_(**kwargs)

    @classmethod
    def get_datasource_by_datasource_instance(
        cls,
        datasource_instance: DataObject,
        **kwargs
    ) -> DataSource:
        datasource_config = datasource_instance.data_source_config
        new_kwargs = dict(datasource_instance.kwargs) if datasource_instance.kwargs else {}
        if kwargs:
            new_kwargs.update(kwargs)
        if datasource_config:
            attributes = list(datasource_config.data_source_config_attributes)
            relationships = list(datasource_config.data_source_config_relationships)
            relationship_config = cls.get_relationship_config_from_data_source_config(
                relationships=relationships,
            )
            amd = data_source_attribute_metadata(data_source_config)
            runtime_fields = cls.get_runtime_fields_from_data_source_config(
                attributes=attributes
            )
            runtime_fields_with_source_order_attributes = \
                cls.add_source_order_to_runtime_fields_attributes(
                    attributes=attributes,
                )
            runtime_fields_with_source_order_relationships = \
                cls.add_source_order_to_runtime_fields_relationships(
                    relationships=relationships,
                )
            new_kwargs.update({
                'relationship_cfg': relationship_config,
                'attribute_metadata': amd,
                'runtime_fields':
                    runtime_fields | runtime_fields_with_source_order_attributes |
                    runtime_fields_with_source_order_relationships
            })
        return DataSourceUtils.get_datasource_by_name(
            datasource_instance.builtin_name,
            **new_kwargs
        )

    @classmethod
    def get_relationship_config_from_data_source_config(
        cls,
        relationships: Iterable[DataObject]
    ) -> dict:
        relationship_cfg = {}
        for rel in relationships:
            for obj_type in [rel.object_type, rel.foreign_object_type]:
                if obj_type not in relationship_cfg:
                    relationship_cfg[obj_type] = {
                        'to_one': {},
                        'to_many': {},
                        'foreign_keys': {}
                    }
            relationship_cfg[rel.object_type]['to_one'][rel.name] = rel.foreign_object_type
            relationship_cfg[rel.foreign_object_type]['to_many'][rel.foreign_name] = \
                rel.object_type
            relationship_cfg[rel.foreign_object_type]['foreign_keys'][rel.foreign_name] = \
                f'{rel.name}.id'
        return {
            k: from_dict(data_class=RelationshipConfig, data=v)
            for k, v in relationship_cfg.items()
        }

    @classmethod
    def get_runtime_fields_from_data_source_config(
        cls,
        attributes: Iterable[DataObject]
    ) -> dict:
        runtime_fields = {}
        for dsa in attributes:
            if dsa.runtime_definition is None:
                continue
            if dsa.object_type not in runtime_fields:
                runtime_fields[dsa.object_type] = {}
            if 'function' in dsa.runtime_definition:
                from ..elastic.runtime_fields import RuntimeFields  # Break circular import cycle
                method = getattr(RuntimeFields, dsa.runtime_definition['function'])
                runtime_fields[dsa.object_type][dsa.name] = \
                    method(**dsa.runtime_definition.get('function_kwargs', {}))
            if 'script' in dsa.runtime_definition:
                runtime_fields[dsa.object_type][dsa.name] = {
                    'type': dsa.runtime_definition.get('type', 'keyword'),
                    'script': {'source': dsa.runtime_definition['script']}
                }
        return runtime_fields

    @classmethod
    def add_source_order_to_runtime_fields_attributes(
        cls,
        attributes: Iterable[DataObject]
    ) -> dict:
        runtime_fields = {}
        for dsra in attributes:
            if dsra.source_order is None:
                continue
            from ..elastic.runtime_fields import RuntimeFields  # Break circular import cycle
            if dsra.object_type not in runtime_fields:
                runtime_fields[dsra.object_type] = {}
            runtime_fields[dsra.object_type][f'{dsra.name}'] = RuntimeFields.coalesce(
                [f'{dsra.name}.provenance.{source_order}.value'
                 for source_order in dsra.source_order]
            )
        return runtime_fields

    @classmethod
    def add_source_order_to_runtime_fields_relationships(
        cls,
        relationships: Iterable[DataObject]
    ) -> dict:
        runtime_fields = {}
        for dsrc in relationships:
            if dsrc.source_order is None:
                continue
            from ..elastic.runtime_fields import RuntimeFields  # Break circular import cycle
            if dsrc.object_type not in runtime_fields:
                runtime_fields[dsrc.object_type] = {}
            runtime_fields[dsrc.object_type][f'{dsrc.name}'] = RuntimeFields.coalesce(
                [f'{dsrc.name}.id.provenance.{source_order}.value'
                 for source_order in dsrc.source_order]
            )
        return runtime_fields

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
        requested_fields: list[str] | None = None
    ) -> Iterator[DataObject]:
        objs = datasource.get_by_ids(object_type, ids, requested_fields=requested_fields)
        if sort_by is not None:
            yield from sorted(objs, key=lambda obj: obj.get_field_by_name(sort_by) or 0)
        else:
            yield from objs
