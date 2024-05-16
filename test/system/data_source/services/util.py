# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from datetime import datetime

from tol.core.relationship import RelationshipConfig
from tol.elastic import ElasticDataSource


def get_prefix() -> str:
    elastic_prefix = os.environ['ELASTIC_INDEX_PREFIX']
    uuid_prefix = os.environ['UUID_PREFIX']
    return f'{elastic_prefix}-test-{uuid_prefix}'


def elastic_datasource(
    class_: ElasticDataSource = ElasticDataSource
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
                    'runtime_column': {
                        'type': 'boolean',
                        'script': """
                            if (doc['bool_column'].size()>0) {
                                emit(!doc['bool_column'].value)
                            }
                        """
                    }
                }
            }
        }
    )


def __get_indices_names() -> None:
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
