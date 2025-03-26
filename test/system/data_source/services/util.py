# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
import time
from datetime import datetime

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
    uuid_prefix = os.environ['UUID_PREFIX']
    return f'{elastic_prefix}-test-{uuid_prefix}'


def elastic_datasource(
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
            'index_prefix': get_prefix(),
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


def __get_indices_names() -> list[str]:
    prefix = get_prefix()
    return [
        f'{prefix}-{type_}' for type_ in (
            'root',
            'related'
        )
    ]


def create_indices() -> None:
    """Creates all indices."""

    indices = __get_indices_names()
    elastic_ds = elastic_datasource()

    elastic_ds.es.indices.create(
        index=indices,
        ignore=[400]
    )


def empty_all_indices() -> None:
    """Empties all indices of all rows"""

    indices = __get_indices_names()
    elastic_ds = elastic_datasource()

    elastic_ds.es.delete_by_query(
        index=indices,
        body={'query': {'match_all': {}}}
    )


def delete_indices() -> None:
    """Deletes all indices"""

    indices = __get_indices_names()
    elastic_ds = elastic_datasource()

    elastic_ds.es.indices.delete(
        index=indices,
        ignore=[400, 404]
    )


def upsert_archetypes() -> None:
    """
    Ensures that `ElasticDataSource().attribute_types`
    is fully populated by upserting an archetypal
    `DataObject` instance for each.
    We do this directly in ElasticSearch to avoid
    a chicken-and-egg situation
    """

    elastic_ds = elastic_datasource()

    elastic_ds.es.index(
        index=get_prefix() + '-root',
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
        index=get_prefix() + '-related',
        id='#REL',
        document={
            'str_column': 'abc',
            'int_column': 42,
            'datetime_column': datetime(2020, 1, 1, 0, 0, 0),
            'bool_column': True,
            'list_column': ['item']
        }
    )
