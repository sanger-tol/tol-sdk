# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

from caseconverter import kebabcase

from tol.core import DataSource

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
        self,
        eds: DataSource,
        mappings: dict,
        dry_run: bool = True
    ):
        base_prefix = self._base_prefix(eds)
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