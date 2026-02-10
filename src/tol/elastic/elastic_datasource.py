# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

from cachetools.func import ttl_cache

from caseconverter import (
    kebabcase,
    snakecase
)

from elasticsearch import (Elasticsearch, helpers)

from .client import ElasticClient
from .converter import (
    ElasticApiConverter,
    ElasticUpdateInputConverter,
    ElasticUpsertInputConverter,
)
from .filter import ElasticFilterConverter
from .parser import ElasticUpdateInputResource, ElasticUpsertInputResource
from ..core import (
    AttributeMetadata,
    DataId,
    DataObject,
    DataSource,
    DataSourceError,
    DataSourceFilter,
    DefaultAttributeMetadata,
    GroupStatterDataLoader
)
from ..core.operator import (
    Aggregator,
    Counter,
    Cursor,
    DetailGetter,
    Enricher,
    GroupStatter,
    ListGetter,
    PageGetter,
    RelationWriteMode,
    Relational,
    Statter,
    Summariser,
    Updater,
    Upserter,
)
from ..core.operator.updater import DataObjectUpdate
from ..core.relationship import (
    RelationshipConfig
)
from ..core.requested_fields import ReqFieldsTree, requested_fields_to_tree

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession

ElasticClientFactory = Callable[[], ElasticClient]
ElasticConverterFactory = Callable[[], ElasticApiConverter]
DataObjectConverterFactory = Callable[[], ElasticUpsertInputConverter]
DataObjectUpdateConverterFactory = Callable[[], ElasticUpdateInputConverter]


class ElasticDataSource(
    DataSource,
    Cursor,
    Summariser,
    DetailGetter,
    Enricher,
    PageGetter,
    ListGetter,
    Aggregator,
    Relational,
    Updater,
    Upserter,
    Counter,
    Statter,
    GroupStatter
):
    def __init__(self, config: dict,
                 client_factory: ElasticClientFactory,
                 elastic_converter_factory: ElasticConverterFactory,
                 data_object_converter_factory: DataObjectConverterFactory,
                 data_object_update_converter_factory: DataObjectUpdateConverterFactory,
                 attribute_metadata: AttributeMetadata = DefaultAttributeMetadata,
                 relationship_cfg: dict[str, RelationshipConfig] | None = None,
                 runtime_fields: dict[str, Any] = {},
                 **kwargs):
        del kwargs
        super().__init__(
            config,
            expected=['uri', 'user', 'password', 'index_prefix'],
            attribute_metadata=attribute_metadata,
        )
        self._client_factory = client_factory
        self._elastic_converter_factory = elastic_converter_factory
        self._data_object_converter_factory = data_object_converter_factory
        self._data_object_update_converter_factory = data_object_update_converter_factory
        """
        relationship_cfg is also supported if we want to handle relationships
        Only FKs pointing to IDs are currently supported
        """
        attribute_metadata.host = self
        self.runtime_fields = runtime_fields
        self._initialise_elasticsearch()
        self.__lazy = False
        self._relationship_cfg = relationship_cfg

    @property
    def lazy_fetch(self) -> bool:
        """
        If `True`, enriched fields will be consulted.

        If `False`, enriched fields will be ignored, and the relation object
        directly fetched by ID, every time.
        """

        return self.__lazy

    @lazy_fetch.setter
    def lazy_fetch(self, new_val: bool) -> None:
        self.__lazy = new_val

    @property
    def _default_write_mode(self) -> RelationWriteMode:
        return RelationWriteMode.FUSED

    def _initialise_elasticsearch(self):
        self.es = Elasticsearch(
            self.uri,
            http_auth=(self.user, self.password),
            timeout=30,
            max_retries=10,
            retry_on_timeout=True
        )
        self.helpers = helpers

    def get_cursor_page(
        self,
        object_type: str,
        page_size: int | None = None,
        object_filters: DataSourceFilter | None = None,
        search_after: list[str] | None = None,
        session: OperableSession | None = None,
        **kwargs,
    ) -> tuple[Iterable[DataObject], list[str] | None]:
        del session, kwargs

        resp = self.__get_page_response(
            object_type,
            object_filters,
            'id',
            page_size,
            search_after=search_after
        )

        return self.__format_cursor_response(resp)

    def upsert(
        self,
        object_type: str,
        objects: Iterable[DataObject],
        chunk_size: int = 100,
        id_func=lambda x: x.id,
        field_prefix: str = '',
        merge_collections: bool | None = None,
        **kwargs
    ) -> None:
        del kwargs

        if merge_collections is False:
            msg = 'ElasticDataSource does not support turning off merge_collections'
            raise DataSourceError(msg)

        index = self.__get_index_or_alias(object_type)
        converter = self._data_object_converter_factory()
        (no_of_operations, no_of_errors) = \
            self.helpers.bulk(self.es,
                              converter.convert(ElasticUpsertInputResource(index,
                                                                           objects,
                                                                           id_func,
                                                                           field_prefix)),
                              stats_only=True,
                              chunk_size=chunk_size)
        if no_of_errors > 0:
            raise DataSourceError(f'{no_of_errors} errors encountered '
                                  f'upserting {no_of_operations} objects')

    def update(
        self,
        object_type: str,
        updates: Iterable[DataObjectUpdate],
        field_prefix: str = '',
        candidate_key: Iterable[str] = [],
        **kwargs
    ) -> None:

        # This tries to find an object in the DataSource that matches
        # the candidate key. If found it will perform the update

        index = self.__get_index_or_alias(object_type)
        real_index_name = self._get_indices().get(index)
        converter = self._data_object_update_converter_factory()
        for (_, update) in updates:
            # converter takes update, returns candidate key and body

            # We can get the candidate key dynamically from the actual update
            if 'candidate_key_func' in kwargs:
                candidate_key = kwargs['candidate_key_func'](update)
            self.es.update_by_query(
                index=real_index_name,
                body=converter.convert(ElasticUpdateInputResource(object_type,
                                                                  update,
                                                                  field_prefix,
                                                                  candidate_key)),
                conflicts='proceed',
                wait_for_completion=False
            )

    def _summarise(
        self,
        summary: DataObject,
        ext_and: dict[str, Any] | None = None,
    ) -> None:

        loader = GroupStatterDataLoader(
            self,
            self,
            [],
            summary.source_object_type,
            summary.destination_object_type,
            'Unmanaged summariser (no audit)',
            object_filters=self._mix_in_ext_and(
                summary.object_filters,
                ext_and,
            ),
            group_statter_group_by=summary.group_by,
            group_statter_stats_fields=summary.stats_fields,
            group_statter_stats=summary.stats,
        )
        loader.load(field_prefix=summary.prefix)

    def __format_cursor_response(
        self,
        resp: dict[str, Any]
    ) -> tuple[Iterable[DataObject], list[str] | None]:

        hits = list(resp['hits']['hits'])
        if not hits:
            return [], None

        search_after = hits[-1]['sort']
        objs = self._elastic_converter_factory().convert_list(hits)

        return objs, search_after

    def __get_index_or_alias(self, object_type: str) -> str:
        return f'{self.index_prefix}-{kebabcase(object_type)}'

    def __get_object_type(self, index: str) -> str:
        start = len(self.index_prefix) + 1
        return snakecase(index[start:])

    def _field_or_keyword(self, object_type: str, name: str):
        """
        Map our field format to Elastic's format
        """
        if name == 'id':
            return 'uid.keyword'
        # Runtime fields don't behave the same as text fields
        if object_type in self.runtime_fields and name in self.runtime_fields[object_type]:
            return name
        # An attribute of the object
        if name in self.attribute_types[object_type]:
            field_type = self.attribute_types[object_type][name]
            if field_type == 'str':
                return f'{name}.keyword'
        if '.' in name:
            rc = self.relationship_config[object_type]
            relationship_name, attribute = name.split('.')[0], name.split('.')[1]
            if attribute == 'id':
                return f'{name}.keyword'
            relationship_object_type = rc.to_one[relationship_name]
            attribute_type = self.attribute_types[relationship_object_type][attribute]
            if attribute_type == 'str':
                return f'{name}.keyword'
        return name

    def _prepare_get_parameters(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None,
        requested_tree: ReqFieldsTree | None = None,
    ) -> tuple[str | None, dict, list[Any] | None, Any | None]:
        """
        Prepares the real_index_name, query, fields, and runtime_mappings,
        needed for all get operations
        """

        index = self.__get_index_or_alias(object_type)
        real_index_name = self._get_indices().get(index)
        query = ElasticFilterConverter(self).convert(object_type, object_filters)
        fields = self.runtime_fields[object_type].keys() \
            if object_type in self.runtime_fields else None
        
        # If there is a requested tree, ensure only fields from this tree
        # are being fetched
        if fields is not None and requested_tree is not None:
            fields = filter(
                lambda field: field in requested_tree,
                fields
            )

        runtime_mappings = self.runtime_fields[object_type] \
            if object_type in self.runtime_fields else None

        return (
            real_index_name,
            query,
            list(fields) if fields is not None else None,  # Consume the `Iterable`
            runtime_mappings,
        )

    @requested_fields_to_tree
    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
        requested_tree: ReqFieldsTree | None = None,
        **kwargs
    ) -> Iterable[DataObject]:
        del kwargs
        f = DataSourceFilter()
        f.and_ = {'_id': {'in_list': {'value': object_ids}}}
        # get_by_id is expected to return objects in the order they were asked for
        # or None if not found, hence the following rearrangement.
        return self.sort_by_id(
            self.get_list(object_type, object_filters=f, requested_tree=requested_tree),
            object_ids
        )

    @requested_fields_to_tree
    def get_list_page(
        self,
        object_type: str,
        page: int,
        object_filters: DataSourceFilter | None = None,
        sort_by: str | None = None,
        page_size: int | None = None,
        requested_tree: ReqFieldsTree | None = None,
        **kwargs
    ) -> tuple[Iterable[DataObject], int]:
        del kwargs

        resp = self.__get_page_response(
            object_type,
            object_filters,
            sort_by,
            page_size,
            page=page,
            requested_tree=requested_tree,
        )

        return (
            self._elastic_converter_factory().convert_list(
                resp['hits']['hits']
            ),
            resp['hits']['total']['value']
        )

    def __get_page_response(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None,
        sort_by: str | None,
        page_size: int | None,
        page: int | None = None,
        search_after: list[Any] | None = None,
        requested_tree: ReqFieldsTree | None = None,
    ) -> dict[str, Any]:
        real_index_name, query, fields, runtime_mappings = self._prepare_get_parameters(
            object_type, object_filters, requested_tree
        )
        sort = self._build_elasticsearch_sort(object_type, sort_by)
        if page_size is None:
            page_size = self.get_page_size()
        from_ = (page - 1) * page_size if page is not None else None
        return self.es.search(
            from_=from_,
            size=page_size,
            index=real_index_name,
            query=query,
            sort=sort,
            fields=fields,
            runtime_mappings=runtime_mappings,
            search_after=search_after
        )

    def _build_elasticsearch_sort(
        self,
        object_type: str,
        sort_by: str | None
    ) -> list[dict[str, str]]:
        default_sort = {'uid.keyword': 'asc'}
        if sort_by is None:
            return [default_sort]
        if sort_by == '-id':
            return self.__build_uid_sort(True)
        if sort_by == 'id':
            return self.__build_uid_sort(False)
        return [
            self.__build_sort(object_type, sort_by),
            default_sort
        ]

    def __build_uid_sort(
        self,
        desc: bool
    ) -> list[dict[str, str]]:

        order = 'desc' if desc else 'asc'
        return [
            {
                'uid.keyword': {
                    'order': order,
                    'unmapped_type': 'keyword'
                }
            }
        ]

    def __build_sort(
        self,
        object_type: str,
        sort_by: str
    ) -> dict[str, str]:

        if sort_by.startswith('-'):
            field = self._field_or_keyword(object_type, sort_by[1:])
            order = 'desc'
        else:
            field = self._field_or_keyword(object_type, sort_by)
            order = 'asc'

        return {field: order}

    @requested_fields_to_tree
    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None = None,
        session: OperableSession | None = None,
        requested_tree: ReqFieldsTree | None = None,
        **kwargs
    ) -> Iterable[DataObject]:
        del session, kwargs

        real_index_name, query, fields, runtime_mappings = self._prepare_get_parameters(
            object_type, object_filters, requested_tree
        )
        generator = self.helpers.scan(self.es,
                                      index=real_index_name,
                                      scroll='10m',
                                      size=500,
                                      query={'query': query},
                                      fields=fields,
                                      runtime_mappings=runtime_mappings)
        return self._elastic_converter_factory().convert_list(generator)

    def get_aggregations(
        self,
        object_type: str,
        aggregations: dict,
        object_filters: DataSourceFilter | None = None,
        **kwargs
    ) -> dict:
        del kwargs

        real_index_name, query, fields, runtime_mappings = self._prepare_get_parameters(
            object_type, object_filters
        )
        resp = self.es.search(
            size=0,
            index=real_index_name,
            query=query,
            aggregations=aggregations,
            fields=fields,
            runtime_mappings=runtime_mappings
        )
        return resp['aggregations']

    def get_stats(
        self,
        object_type: str,
        stats_fields: list[str] = [],
        stats: list[str] = [],
        object_filters: DataSourceFilter | None = None,
        **kwargs
    ):
        del kwargs
        aggs = self.__get_aggs(
            object_type=object_type,
            stats_fields=stats_fields,
            stats=stats)
        agg_results = self.get_aggregations(
            object_type=object_type,
            aggregations=aggs,
            object_filters=object_filters
        )
        return self.__get_data_from_stats_aggregation(
            aggregation_result=agg_results,
            object_type=object_type,
            stats_fields=stats_fields,
            stats=stats
        )

    def __get_data_from_stats_aggregation(
            self,
            aggregation_result,
            object_type,
            stats_fields,
            stats
    ):
        stats_values = {}
        for stats_field in stats_fields:
            stats_values[stats_field] = {}
            for stat in stats:
                stat_value = aggregation_result[f'{stats_field}_{stat}']['value']
                python_type = self.attribute_types[object_type][stats_field]
                if python_type == 'datetime' and stat_value is not None \
                        and stat in ['min', 'max']:
                    stat_value = datetime.fromtimestamp(stat_value / 1000)
                stats_values[stats_field][stat] = stat_value
        return {'stats': stats_values}

    def get_group_stats(
        self,
        object_type: str,
        group_by: list[str],
        stats_fields: list[str] = [],
        stats: list[str] = [],
        object_filters: DataSourceFilter | None = None,
        **kwargs
    ) -> Iterable[dict[Any, int]]:
        del kwargs

        after_key = None
        while True:
            after_key, buckets = self.__get_group_stats_page(
                object_type,
                group_by,
                stats_fields=stats_fields,
                stats=stats,
                object_filters=object_filters,
                after_key=after_key)
            if len(buckets) == 0:
                break
            yield from buckets

    def __get_group_stats_page(
        self,
        object_type: str,
        group_by: list[str],
        stats_fields: list[str] = [],
        stats: list[str] = [],
        after_key: str | None = None,
        object_filters: DataSourceFilter | None = None,
    ):
        # This will return a potentially large set of results, so we need
        # to page through them
        aggregation = {
            'counts': {
                'composite': {
                    'sources': [{
                        field: {
                            'terms': {
                                'field': self._field_or_keyword(object_type, field)
                            }
                        }
                    } for field in group_by]
                },
            }
        }
        if stats_fields is not None:
            aggregation['counts']['aggregations'] = self.__get_aggs(
                object_type,
                stats_fields,
                stats
            )
        if after_key is not None:
            aggregation['counts']['composite']['after'] = after_key
        agg_page = self.get_aggregations(
            object_type,
            aggregations=aggregation,
            object_filters=object_filters)
        after_key, buckets = self.__get_data_from_group_stats_aggregation(
            agg_page,
            object_type,
            stats_fields,
            stats
        )
        return after_key, buckets

    def __get_aggs(
            self,
            object_type: str,
            stats_fields: list,
            stats: list
    ):
        ret = {}
        for stats_field in stats_fields:
            for stat in stats:
                agg = {stat: {'field': self._field_or_keyword(object_type, stats_field)}}
                if stat == 'union':
                    # This is a bespoke aggregation
                    agg = self.__get_union_aggregation(object_type, stats_field)
                elif stat == 'unique':
                    agg = self.__get_unique_count_aggregation(object_type, stats_field)
                elif self.attribute_types[object_type][stats_field] == 'str' \
                        and stat in ['min', 'max']:
                    agg = self.__get_string_aggregation(object_type, stats_field, stat)
                ret[f'{stats_field}_{stat}'] = agg
        return ret

    def __get_data_from_group_stats_aggregation(
            self,
            aggregation_result,
            object_type,
            stats_fields,
            stats
    ):
        # The after_key is sent back in one request and we use it as-is in the next request
        after_key = None
        if 'after_key' in aggregation_result['counts']:
            after_key = aggregation_result['counts']['after_key']
        buckets = aggregation_result['counts']['buckets']
        # all_stats looks like:
        # [{'key': {'first_group_by': 'value_of_first_group_by'}
        #           'second_group_by': 'value_of_second_group_by'},
        #   'stats': {'count': 123,
        #             'stats_field_stat': 345}}]
        all_stats = []
        for v in buckets:
            stats_values = {'count': v['doc_count']}
            for stats_field in stats_fields:
                stats_values[stats_field] = {}
                for stat in stats:
                    stat_value = v[f'{stats_field}_{stat}']['value']
                    python_type = self.attribute_types[object_type][stats_field]
                    if python_type == 'datetime' and stat_value is not None \
                            and stat in ['min', 'max']:
                        stat_value = datetime.fromtimestamp(stat_value / 1000)
                    stats_values[stats_field][stat] = stat_value
            all_stats.append({'key': v['key'], 'stats': stats_values})

        return after_key, all_stats

    def __get_union_aggregation(self, object_type, field):
        """
        This function is building up a union of all elements of a list in
        the aggregated field
        init_script: This is what is run at the start of each bucket
        map_script: This builds up a list, PER SHARD, of the elements in all
        records in the bucket
        combine_script: This just returns the per-shard list in our case
        reduce_script: This combines the per-shard lists into the final list
        See information on scripted metrics for Elastic for more details
        """
        field_or_keyword = self._field_or_keyword(object_type, field)
        agg = {
            'scripted_metric': {
                'init_script': 'state.list = []',
                'map_script': f"""
                    for (element in doc['{field_or_keyword}']) {{
                        if (!state.list.contains(element)) {{
                            state.list.add(element)
                        }}
                    }}
                """,
                'combine_script': 'return state.list',
                'reduce_script': """
                    ArrayList ret = [];
                    for (a in states) {
                        for (element in a) {
                            if (!ret.contains(element)) {
                                ret.add(element)
                            }
                        }
                    }
                    return ret;
                """
            }
        }
        return agg

    def __get_string_aggregation(self, object_type, field, stat):
        """
        This function is calculating the min and max of a string

        """
        field_or_keyword = self._field_or_keyword(object_type, field)
        comparator = '>'
        if stat == 'min':
            comparator = '<'
        agg = {
            'scripted_metric': {
                'init_script': 'state.stat = null',
                'map_script': f"""
                    for (ss in doc['{field_or_keyword}']) {{
                        if (state.stat == null) {{
                            state.stat = ss; continue
                        }}
                        if (ss.compareTo(state.stat) {comparator} 0) {{
                            state.stat = ss
                        }}
                    }}
                    """,
                'combine_script': 'return state.stat',
                'reduce_script': f"""
                    String ret = null;
                    for (a in states) {{
                        if (a == null) {{
                            continue
                        }}
                        if (ret == null) {{
                            ret = a;
                            continue
                        }}
                        if (a.compareTo(ret) {comparator} 0) {{
                            ret = a
                        }}
                    }}
                    return ret;
                """
            }
        }
        return agg

    def __get_unique_count_aggregation(self, object_type, field):
        """
        This function is calculating the unique values in the given field

        """
        field_or_keyword = self._field_or_keyword(object_type, field)
        agg = {
            'scripted_metric': {
                'params': {
                    'fieldName': field_or_keyword
                },
                'init_script': 'state.list = []',
                'map_script': """
                    if(doc[params.fieldName].size() > 0) {
                        state.list.add(doc[params.fieldName].value);
                    }
                    """,
                'combine_script': 'return state.list;',
                'reduce_script': """
                    Map uniqueValueMap = new HashMap();
                    int count = 0;
                    for(shardList in states) {
                        if(shardList != null) {
                            for(key in shardList) {
                                if(!uniqueValueMap.containsKey(key)) {
                                    count +=1;
                                    uniqueValueMap.put(key, key);
                                }
                            }
                        }
                    }
                    return count;
                """
            }
        }
        return agg

    def get_count(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None = None,
        **kwargs
    ) -> int:
        del kwargs

        real_index_name, query, fields, runtime_mappings = self._prepare_get_parameters(
            object_type, object_filters
        )
        # We are not using es.count so that we can use runtime fields
        resp = self.es.search(
            index=real_index_name,
            track_total_hits=True,
            size=0,
            query=query,
            fields=fields,
            runtime_mappings=runtime_mappings
        )
        return resp['hits']['total']['value']

    @ttl_cache(ttl=3600)
    def _get_indices(self) -> dict[str, str]:
        # Get all as the actual indexes may not have the correct prefix
        results = self.es.indices.get_alias('*')
        aliased_indexes = {
            alias: index
            for index, aliases in results.items()
            for alias in aliases.get('aliases', {}).keys()
            if alias.startswith(self.index_prefix)
        }
        # Non-aliased indexes
        non_aliased_indexes = {
            index: index
            for index in results.keys()
            if index.startswith(self.index_prefix)
        }
        return aliased_indexes | non_aliased_indexes

    def _real_index_to_object_type(self, index: str) -> str:
        aliases = self._get_indices()
        alias = next((k for k, v in aliases.items() if v == index), None)
        return self.__get_object_type(alias) if alias else None

    @property
    def supported_types(self):
        indexes = self._get_indices()
        return [self.__get_object_type(index_name)
                for index_name in indexes.keys()]

    def __map_type(self, type_: str) -> str:
        if type_ in ['text', 'keyword']:
            return 'str'
        if type_ == 'long':
            return 'int'
        if type_ == 'date':
            return 'datetime'
        if type_ == 'boolean':
            return 'bool'
        return type_

    def _get_attribute_types_for_object_type(self, object_type: str) -> dict:
        index_or_alias_name = self.__get_index_or_alias(object_type)
        real_index_name = self._get_indices().get(index_or_alias_name)
        mapping = self.es.indices.get_mapping(index=index_or_alias_name)
        if 'properties' not in mapping[real_index_name]['mappings']:
            return {}
        properties = mapping[real_index_name]['mappings']['properties']
        standard_types = {
            'id' if property_name == 'uid' else property_name:
                self.__map_type(properties[property_name]['type'])
            for property_name in properties
            if 'type' in properties[property_name]
        }
        runtime_types = {
            name: self.__map_type(self.runtime_fields[object_type][name]['type'])
            for name in self.runtime_fields[object_type].keys()
        } if object_type in self.runtime_fields else {}
        return standard_types | runtime_types

    @property
    @ttl_cache(ttl=3600)
    def attribute_types(self) -> dict[str, dict[str, str]]:
        return {
            t: self._get_attribute_types_for_object_type(t)
            for t in self.supported_types
        }

    @property
    def relationship_config(self) -> dict[str, RelationshipConfig]:
        return self._relationship_cfg

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str,
        **kwargs
    ) -> DataObject | None:
        del kwargs

        self.__validate_to_one_relation(source)

        if self.lazy_fetch and relationship_name in source._to_one_objects:
            return source._to_one_objects.get(relationship_name)

        to_one = self.relationship_config[source.type].to_one

        if relationship_name not in to_one:
            raise DataSourceError('Bad relationship name')

        new_source: DataObject = self.get_one(source.type, source.id)

        local_relation = new_source._to_one_objects.get(relationship_name)
        if local_relation is None:
            return None

        if self.lazy_fetch:
            return local_relation

        target_type = to_one[relationship_name]
        target_id = local_relation.id
        return self.get_one(target_type, target_id)

    def get_to_many_relations(
        self,
        source: DataObject,
        relationship_name: str,
        **kwargs
    ) -> Iterable[DataObject]:
        del kwargs

        if self.relationship_config is None:
            raise DataSourceError('There are no relationships defined')
        relationship_config = self.relationship_config[source.type]
        related_object_type = relationship_config.to_many[relationship_name]
        related_object_fk_attribute = relationship_config.foreign_keys[relationship_name]

        # Get all the related objects that point to this source object
        f = DataSourceFilter()
        f.and_ = {related_object_fk_attribute: {'eq': {'value': source.id}}}
        related_objects = self.get_list(related_object_type, object_filters=f)
        return related_objects

    def __validate_to_one_relation(self, source: DataObject) -> None:
        if self.relationship_config is None:
            raise DataSourceError('There are no relationships defined')

        if source.type not in self.relationship_config:
            raise DataSourceError('This type has no relationships')
