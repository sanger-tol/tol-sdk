# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

from caseconverter import kebabcase

from tol.core import (
    DataObject,
    DataSource,
    DataSourceFilter
)


class ElasticUtils:

    @staticmethod
    def _base_prefix(eds: DataSource) -> str:
        """Strip the trailing environment segment from eds.index_prefix.

        e.g. 'user-data-tol-portal-production' -> 'user-data-tol-portal'
        """
        return eds.index_prefix.rsplit('-', 1)[0]

    @classmethod
    def create_index_set(
        cls,
        eds: DataSource,
        build_number: str,
        dry_run: bool = True
    ):
        """
        Create a set of indices for the given build number, one for each supported object type.
        The index names are in the format '{base_prefix}-{build_number}-{object_type}'.
        If dry_run is True, the index names will be printed instead of actually creating the
        indices.
        """
        base_prefix = cls._base_prefix(eds)
        for object_type in eds.supported_types:
            index_name = f'{base_prefix}-{build_number}-{kebabcase(object_type)}'
            if dry_run:
                print(f'CREATE INDEX: {index_name}')
            else:
                eds.es.indices.create(
                    index=f'{index_name}'
                )

    @classmethod
    def delete_index_set(
        cls,
        eds: DataSource,
        build_number: str,
        dry_run: bool = True
    ):
        """
            Delete a set of indices for the given build number, one for each supported object type.
        """
        base_prefix = cls._base_prefix(eds)
        for object_type in eds.supported_types:
            index_name = f'{base_prefix}-{build_number}-{kebabcase(object_type)}'
            if dry_run:
                print(f'DELETE INDEX: {index_name}')
            else:
                eds.es.indices.delete(
                    index=f'{index_name}'
                )

    @classmethod
    def update_aliases(
        cls,
        eds: DataSource,
        mappings: dict,
        dry_run: bool = True
    ):
        """
        Update aliases for the given mappings.
        """
        base_prefix = cls._base_prefix(eds)
        aliases = []
        for object_type in eds.supported_types:
            for env, mapping in mappings.items():
                aliases.extend([
                    {
                        'remove': {
                            'index': f'{base_prefix}-{mapping["old"]}-{kebabcase(object_type)}',
                            'alias': f'{base_prefix}-{env}-{kebabcase(object_type)}'
                        }
                    },
                    {
                        'add': {
                            'index': f'{base_prefix}-{mapping["new"]}-{kebabcase(object_type)}',
                            'alias': f'{base_prefix}-{env}-{kebabcase(object_type)}'
                        }
                    }
                ])
        if dry_run:
            print(json.dumps(aliases, indent=2))
        else:
            eds.es.indices.update_aliases({
                'actions': aliases
            })

    @classmethod
    def enrich_objects(
        cls,
        eds: DataSource,
        object_type: str,
        ids: list[str]
    ) -> None:
        """
            Use the objects with the given IDs to enrich all their related (child) objects
        """
        for target_object_type in eds.relationships_to_enrich[object_type].keys():
            source_objects = eds.get_by_ids(object_type, ids)
            eds.enrich(object_type, source_objects, target_object_type)

    @classmethod
    def summarise_objects(
            cls,
            eds: DataSource,
            portaldb_ds: DataSource,
            object_type: str,
            ids: list[str],
            data_source_instance: DataObject) -> None:
        """
            Use the objects with the given IDs to summarise all their related (parent) objects
        """
        f = DataSourceFilter()
        f.and_ = {
            'source_object_type': {'eq': {'value': object_type}},
            'data_source_config.id': {'eq': {'value': data_source_instance.data_source_config.id}}
        }
        summaries = list(portaldb_ds.get_list('data_source_config_summary', object_filters=f))

        changes = eds.resummarise_by_ids(
            summaries,
            source_object_type=object_type,
            source_object_ids=ids
        )

        return changes
