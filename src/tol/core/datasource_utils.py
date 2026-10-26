# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import importlib
from typing import Iterable, Iterator, cast

from dacite import from_dict

from .data_object import DataObject
from .data_source_attribute_metadata import data_source_attribute_metadata
from .datasource import DataSource
from .datasource_error import DataSourceError
from .datasource_filter import DataSourceFilter
from .operator.provenancer import ProvenanceField, ProvenanceFields
from .relationship import RelationshipConfig
from .runtime_fields import RuntimeField


class DataSourceUtils:

    @classmethod
    def get_datasource(
        cls,
        datasource_instance_id: str,
        config_datasource: DataSource | None = None,
        direct: bool = False
    ) -> DataSource:
        if config_datasource is None:
            from ..sources.quasar import quasar
            config_datasource = quasar()
        datasource_instance = config_datasource.get_one(
            'data_source_instance',
            datasource_instance_id
        )
        if datasource_instance is None:
            raise DataSourceError(
                f'Datasource instance with id {datasource_instance_id} not found'
            )
        return cls.get_datasource_by_datasource_instance(
            datasource_instance,
            direct=direct
        )

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
        direct: bool = False,
        **kwargs
    ) -> DataSource:
        datasource_config = datasource_instance.data_source_config
        source_kwargs = (
            datasource_instance.api_kwargs
            if not direct and datasource_instance.api_name  # The test is for the name being set
            else datasource_instance.direct_kwargs
        )
        new_kwargs = dict(source_kwargs) if source_kwargs else {}
        if kwargs:
            new_kwargs.update(kwargs)
        if datasource_config:
            attributes = list(datasource_config.data_source_config_attributes)
            relationships = list(datasource_config.data_source_config_relationships)
            relationship_config = cls.get_relationship_config_from_data_source_config(
                relationships=relationships,
            )
            amd = data_source_attribute_metadata(datasource_config)
            runtime_fields = cls.get_runtime_fields_from_data_source_config(
                attributes=attributes
            )
            new_kwargs.update({
                'relationship_cfg': relationship_config,
                'attribute_metadata': amd,
                'runtime_fields': runtime_fields,
                'provenance_fields': cls.get_provenance_fields(
                    attributes=attributes,
                    relationships=relationships
                ),
            })

        datasource_name = (
            datasource_instance.api_name
            if not direct and datasource_instance.api_name
            else datasource_instance.direct_name
        )
        return DataSourceUtils.get_datasource_by_name(
            datasource_name,
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
    ) -> dict[str, dict[str, RuntimeField]]:
        # A dictionary grouping runtime fields by object type,
        # then their name within that object type
        runtime_fields: dict[str, dict[str, RuntimeField]] = {}

        # Loop through each attribute config and form a `RuntimeField` from it
        # (each `dsa` corresponds to a row in the `data_source_config_attribute` table)
        for dsa in attributes:
            # For typing purposes, extract the name and object type from `dsa`.
            # `DataObject` assumes any attribute can be `None`, but the corresponding columns
            # in the database for these attribute are NOT NULL
            object_type = cast(str, dsa.object_type)
            name = cast(str, dsa.name)

            # If there's no runtime definition for this field, then it's not a runtime field
            # (just a regular attribute), so skip it
            if dsa.runtime_definition is None:
                continue

            # If we haven't seen this object type yet, create its dictionary in `runtime_fields`
            if dsa.object_type not in runtime_fields:
                runtime_fields[object_type] = {}

            # Add a `RuntimeField` to `runtime_fields`.
            # I've done this in two branches, rather than using `.get` each time in a single
            # `RuntimeField` construction, because it ensures that every runtime field made
            # is function OR script runtime field. Having both a script and function definition
            # is not a problem, but having a mixture of the two is.
            if 'function' in dsa.runtime_definition:
                runtime_fields[object_type][name] = RuntimeField(
                    type=dsa.runtime_definition['type'],
                    function=dsa.runtime_definition['function'],
                    function_kwargs=dsa.runtime_definition.get('function_kwargs', {}),
                )
            elif 'script' in dsa.runtime_definition:
                runtime_fields[object_type][name] = RuntimeField(
                    type=dsa.runtime_definition.get('type', 'keyword'),
                    script=dsa.runtime_definition['script']
                )
            else:
                # Invalid variant
                raise DataSourceError('Invalid runtime field defintion', (
                    'The JSON defition of a runtime field should have either a "function" key '
                    'or a "script" key'
                ))

        return runtime_fields

    @classmethod
    def get_provenance_fields(cls, attributes, relationships) -> ProvenanceFields:
        provenance_fields = {}
        for dsca, suffix in [(d, '') for d in attributes] + [(d, '.id') for d in relationships]:
            if dsca.source_order is None:
                continue
            if dsca.object_type not in provenance_fields:
                provenance_fields[dsca.object_type] = {}
            provenance_fields[dsca.object_type][f'{dsca.name}{suffix}'] = ProvenanceField(
                source_order=dsca.source_order,
                return_type=None
            )
        return provenance_fields

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
