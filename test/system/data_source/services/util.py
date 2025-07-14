# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
import time
from datetime import datetime
from uuid import uuid4

import requests
from requests.exceptions import ConnectionError

from tol.core.relationship import RelationshipConfig
from tol.elastic import (
    ElasticDataSource,
    RuntimeField
)


def wait_for_ready(seconds: int = 60) -> None:
    elastic_uri = os.environ['ELASTIC_URI']

    for _ in range(seconds):
        try:
            r = requests.get(elastic_uri)
            if r.ok:
                return
        except ConnectionError:
            pass
        finally:
            time.sleep(1)

    raise Exception(
        'The elasticsearch cluster was not ready after '
        f'{seconds} seconds.'
    )


def get_prefix() -> str:
    elastic_prefix = os.environ['ELASTIC_INDEX_PREFIX']
    return f'{elastic_prefix}-test'


def elastic_datasource(
    prefix: str,
    class_: type[ElasticDataSource] = ElasticDataSource
) -> ElasticDataSource:

    rc_root = RelationshipConfig()
    rc_root.to_one = {
        'related_object': 'related'
    }

    return class_(
        {
            'uri': os.environ['ELASTIC_URI'],
            'user': os.environ['ELASTIC_USER'],
            'password': os.environ['ELASTIC_PASSWORD'],
            'index_prefix': prefix,
            'relationship_cfg': {'root': rc_root},
            'runtime_fields': {
                'root': {
                    'runtime_column': RuntimeField(
                        field_type='boolean',
                        dependencies=['bool_column'],
                        function_body="emit(!doc['bool_column'].value)"
                    ).to_dict(),
                },
                'related': {
                    'summarise_one_root_int_column_min': {'type': 'double'},
                    'summarise_one_root_int_column_max': {'type': 'double'},
                }
            }
        }
    )


def __get_indices_names(prefix: str) -> dict[str, str]:
    # Returns dict of index_actual_name to index_alias_name
    uuid = uuid4().hex
    return {
        f'{prefix}-{uuid}-{type_}': f'{prefix}-{type_}' for type_ in (
            'root',
            'related'
        )
    }


def create_indices(prefix: str) -> None:
    """Creates all indices."""

    indices = __get_indices_names(prefix)
    elastic_ds = elastic_datasource(prefix)

    for index, alias in indices.items():
        elastic_ds.es.indices.create(
            index=index,
            aliases={alias: {}},
        )


def delete_indices(prefix: str) -> None:
    """Deletes all indices"""
    elastic_ds = elastic_datasource(prefix)

    matcher = f'{prefix}*'

    elastic_ds.es.indices.delete_alias(
        index=[matcher],
        name=[matcher],
        ignore=[400, 404],
    )

    elastic_ds.es.indices.delete(
        index=[matcher],
        ignore=[400, 404],
    )


def upsert_archetypes(prefix: str) -> None:
    """
    Ensures that `ElasticDataSource().attribute_types`
    is fully populated by upserting an archetypal
    `DataObject` instance for each.
    We do this directly in ElasticSearch to avoid
    a chicken-and-egg situation
    """

    elastic_ds = elastic_datasource(prefix)
    import logging; logging.error(elastic_ds.es.indices.get_alias(index="*"))


    elastic_ds.es.index(
        index=prefix + '-root',
        id='#YOLO',
        document={
            'str_column': 'abc',
            'int_column': 42,
            'datetime_column': datetime(2020, 1, 1, 0, 0, 0),
            'bool_column': True,
            'list_column': ['item'],
            'related_object': {
                'id': '#REL',
                'int_column': 42,
                'datetime_column': datetime(2021, 1, 1, 0, 0, 0)
            },
        }
    )
    elastic_ds.es.index(
        index=prefix + '-related',
        id='#REL',
        document={
            'str_column': 'abc',
            'int_column': 42,
            'datetime_column': datetime(2020, 1, 1, 0, 0, 0),
            'bool_column': True,
            'list_column': ['item']
        }
    )
