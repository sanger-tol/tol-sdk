# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
import time
from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4


from elasticsearch import Elasticsearch

import requests

from tol.core import DataSourceUtils
from tol.core.relationship import RelationshipConfig
from tol.elastic import (
    ElasticDataSource,
    RuntimeField,
    create_elastic_datasource
)


def wait_for_ready(seconds: int = 120) -> None:
    elastic_uri = os.environ['ELASTIC_URI']

    for _ in range(seconds):
        try:
            # When a tuple is passed to the timeout parameter of get(), the first
            # element is the connect timeout, and the second is the read
            # timeout.
            r = requests.get(elastic_uri, timeout=(0.1, 5))
            r.raise_for_status()
            return
        except requests.exceptions.ConnectionError:
            pass
        finally:
            time.sleep(1)

    msg = f'The elasticsearch cluster was not ready after {seconds} seconds.'
    raise Exception(msg)


def get_prefix(extra_prefix: str = 'test') -> str:
    elastic_prefix = os.environ['ELASTIC_INDEX_PREFIX']
    extra = '' if not extra_prefix else f'-{extra_prefix}'
    return f'{elastic_prefix}{extra}'


def elastic_datasource(
    prefix: str,
) -> ElasticDataSource:

    rc_root = RelationshipConfig()
    rc_root.to_one = {
        'related_object': 'related'
    }
    attributes = []
    for obj_type, att in [
        ('root', 'str_column'),
        ('root', 'int_column'),
        ('root', 'datetime_column'),
        ('root', 'bool_column'),
        ('root', 'list_column'),
        ('related', 'str_column'),
        ('related', 'int_column'),
        ('related', 'datetime_column'),
        ('related', 'bool_column'),
        ('related', 'list_column'),
        ('related', 'root_int_column_min'),
        ('related', 'root_int_column_max'),
    ]:
        mock_data_source_config_attribute = Mock()
        mock_data_source_config_attribute.source_order = [
            'source1',
            'source2',
            'source3',
            'source4'
        ]
        mock_data_source_config_attribute.object_type = obj_type
        mock_data_source_config_attribute.name = att
        attributes.append(mock_data_source_config_attribute)

    mock_data_source_config = Mock()
    mock_data_source_config_relationship = Mock()
    mock_data_source_config_relationship.source_order = [
        'source1',
        'source2',
        'source3',
        'source4'
    ]
    mock_data_source_config_relationship.object_type = 'root'
    mock_data_source_config_relationship.name = 'related_object'
    relationships = [
        mock_data_source_config_relationship
    ]
    provenance_runtime_fields_attributes = \
        DataSourceUtils.add_source_order_to_runtime_fields_attributes(attributes)
    provenance_runtime_fields_relationships = \
        DataSourceUtils.add_source_order_to_runtime_fields_relationships(relationships)
    rtf = {
        'root': {
            'runtime_column': RuntimeField(
                field_type='boolean',
                dependencies=['bool_column'],
                function_body="emit(!doc['bool_column'].value)"
            ).to_dict(),
        } | provenance_runtime_fields_attributes.get('root', {}) | provenance_runtime_fields_relationships.get('root', {}),
        'related': {
            'root_int_column_min': {'type': 'double'},
            'root_int_column_max': {'type': 'double'},
        } | provenance_runtime_fields_attributes.get('related', {}) | provenance_runtime_fields_relationships.get('related', {})
    }

    return create_elastic_datasource(
        {
            'uri': os.environ['ELASTIC_URI'],
            'user': os.environ['ELASTIC_USER'],
            'password': os.environ['ELASTIC_PASSWORD'],
            'index_prefix': prefix
        },
        relationship_cfg={'root': rc_root},
        runtime_fields=rtf
    )


def __get_indices_names(prefix: str) -> dict[str, str]:
    # Returns dict of index_actual_name to index_alias_name
    uuid = uuid4().hex

    return {
        f'index-{prefix}-{uuid}-{type_}': f'{prefix}-{type_}'
        for type_ in ('root', 'related')
    }


def __wait_for_alias(
    es: Elasticsearch,
    alias: str,
    expected_index: str,
    timeout: float
) -> None:

    start = time.time()
    while time.time() - start < timeout:
        try:
            result = es.indices.get_alias(name=alias)
            if list(result.keys()) == [expected_index]:
                return
        except Exception:
            pass
        time.sleep(0.05)
    raise TimeoutError(f'Alias {alias} did not point to {expected_index} in time.')


def create_indices(prefix: str, timeout: float = 5) -> None:
    """Creates all indices."""

    indices = __get_indices_names(prefix)
    elastic_ds = elastic_datasource(prefix)

    for index, alias in indices.items():
        elastic_ds.es.indices.create(
            index=index,
        )
        elastic_ds.es.indices.update_aliases(
            body={
                'actions': [
                    {'remove': {'alias': alias, 'index': '*'}},
                    {'add': {'alias': alias, 'index': index}},
                ]
            }
        )

    for index, alias in indices.items():
        __wait_for_alias(elastic_ds.es, alias, index, timeout)
        elastic_ds.es.indices.refresh(index=index)

    elastic_ds.es.indices.refresh(index=['*'])


def delete_aliases(prefix: str, ignore: list[int] | None = None) -> None:
    """Deletes all aliases, leaves the indices"""

    if ignore is None:
        ignore = []

    elastic_ds = elastic_datasource(prefix)

    matcher = f'{prefix}*'

    elastic_ds.es.indices.delete_alias(
        index=['*'],
        name=[matcher],
        ignore=ignore,
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

    elastic_ds.es.index(
        index=prefix + '-root',
        id='#YOLO',
        document={
            'str_column': 'abc',
            'int_column': 42,
            'datetime_column': datetime(2020, 1, 1, 0, 0, 0),
            'bool_column': True,
            'list_column': ['item'],
            # 'dict_column': {'key1': 1},  # dict columns not yet supported in API
            'related_object': {
                'id': {
                    'provenance': {'prov_1': {'value': 1}},
                    'value': 1
                },
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
            'list_column': ['item'],
            # 'dict_column': {'key1': 1},
        }
    )


def wait_for_delete(
    es: Elasticsearch,
    prefix: str,
    timeout: float = 1.0,
    poll_interval: float = 0.1
) -> None:

    start_time = time.time()

    while True:
        aliases = es.indices.get_alias(name='*', ignore=[404])

        matching_aliases = [
            alias for alias_info in aliases.values()
            for alias in alias_info.get('aliases', {})
            if alias.startswith(prefix)
        ]

        if not matching_aliases:
            es.indices.refresh(index=['*'])
            return

        if time.time() - start_time >= timeout:
            raise Exception(
                'Timed out waiting for there to be no aliases '
                f'beginning with {prefix}. Matches:\n'
                f'{matching_aliases}'
            )

        time.sleep(poll_interval)
