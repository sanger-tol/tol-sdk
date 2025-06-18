# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from collections.abc import Callable
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from cachetools.func import ttl_cache

from caseconverter import (
    kebabcase,
    snakecase
)

from dateutil import parser

from elasticsearch import (Elasticsearch, helpers)

from more_itertools import seekable

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

if typing.TYPE_CHECKING:
    from ..core.session import OperableSession


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

    def __init__(self, config: Dict,
                 attribute_metadata: AttributeMetadata = DefaultAttributeMetadata):
        super().__init__(config,
                         expected=['uri', 'user', 'password',
                                   'index_prefix', 'relationship_cfg',
                                   'runtime_fields'],
                         attribute_metadata=attribute_metadata)
        """
        relationship_cfg is also supported if we want to handle relationships
        Only FKs pointing to IDs are currently supported
        """
        attribute_metadata.host = self
        self._initialise_elasticsearch()
        self.__lazy = False

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

    def _convert_data_object_to_dict(self, data_object: DataObject) -> Dict:
        to_ones_dict = {
            k: self._convert_to_one_relation(v)
            for k, v in data_object._to_one_objects.items()
        }
        return data_object.attributes | to_ones_dict

    def _convert_data_objects_in_update_to_dict(self, dict_: Dict) -> Dict:
        ret = {}
        for k, v in dict_.items():
            if isinstance(v, DataObject):
                ret[k] = self._convert_to_one_relation(v)
            else:
                ret[k] = v
        return ret

    def _convert_to_one_relation(
        self,
        one_relation: DataObject | None
    ) -> dict[str, Any] | None:

        if one_relation is None:
            return None

        return {
            'id': one_relation.id,
            **one_relation.attributes
        }

    def _prefix_fields(self, dict_: Dict, prefix: str) -> Dict:
        if prefix == '':
            return dict_
        ret = {}
        for k, v in dict_.items():
            ret[prefix + '_' + k] = v
        return ret

    def _add_uid(self, dict_: Dict, uid: Any) -> Dict:
        return {**dict_, 'uid': f'{uid}'}

    def _convert_dates(self, dict_: Dict) -> Dict:
        ret = {}
        for k, v in dict_.items():
            if isinstance(v, datetime):
                ret[k] = v.isoformat()
            else:
                ret[k] = v
        return ret

    def _stringify_ids(self, dict_: Dict) -> Dict:
        ret = {}
        for k, v in dict_.items():
            if isinstance(v, dict):
                if 'id' in v:
                    v['id'] = str(v['id'])
                ret[k] = self._stringify_ids(v)
            else:
                ret[k] = v

        return ret

    def _action_for_upsert(self, index: str, objects: Iterable[DataObject], id_func: Callable,
                           field_prefix: str):
        real_index_name = self._get_indices().get(index)
        for object_ in objects:
            obj = self._convert_data_object_to_dict(object_)
            obj = self._convert_dates(obj)
            obj = self._prefix_fields(obj, field_prefix)
            obj = self._stringify_ids(obj)
            uid = id_func(object_)
            obj = self._add_uid(obj, uid)
            yield {
                '_op_type': 'update',
                'scripted_upsert': True,
                'upsert': {},
                '_index': real_index_name,
                '_id': uid,
                'script': {
                    'source': self._upsert_script,
                    'lang': 'painless',
                    'params': {
                        'upsertWith': obj
                    }
                }
            }

    def get_cursor_page(
        self,
        object_type: str,
        page_size: Optional[int] = None,
        object_filters: Optional[DataSourceFilter] = None,
        search_after: list[str] | None = None,
        session: Optional[OperableSession] = None
    ) -> tuple[Iterable[DataObject], list[str] | None]:

        resp = self.__get_page_response(
            object_type,
            self.update_cursor_filters(
                search_after,
                object_filters
            ),
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
        **kwargs
    ) -> None:

        index = self.__get_index_or_alias(object_type)
        (no_of_operations, no_of_errors) = \
            self.helpers.bulk(self.es,
                              self._action_for_upsert(index,
                                                      objects,
                                                      id_func,
                                                      field_prefix),
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
        for (_, update) in updates:
            # We can get the candidate key dynamically from the actual update
            if 'candidate_key_func' in kwargs:
                candidate_key = kwargs['candidate_key_func'](update)
            self.es.update_by_query(
                index=real_index_name,
                body=self._action_for_update(object_type,
                                             update,
                                             field_prefix,
                                             candidate_key),
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
        objs = self._convert_dict_to_data_objects(hits)

        return objs, search_after

    @property
    def _update_script(self):
        s = """
            for (param in params['upsertWith'].entrySet()) {
                if (param.value != null) {
                    if (ctx._source[param.key] instanceof Map) {
                        for (newParam in param.value.entrySet()) {
                            ctx._source[param.key][newParam.key] = newParam.value;
                        }
                        continue
                    }
                    if (ctx._source[param.key] instanceof ArrayList) {
                        for (newParam in param.value) {
                            if(! ctx._source[param.key].contains(newParam)) {
                                ctx._source[param.key].add(newParam)
                            }
                        }
                        continue
                    }
                }
                ctx._source[param.key] = param.value;
            }
        """
        return s.replace('\n', ' ')

    @property
    def _upsert_script(self):
        s = f"""
            if ( ctx.op == 'create' ) {{
                ctx._source = params['upsertWith']
            }} else {{
                {self._update_script}
            }}
        """
        return s.replace('\n', ' ')

    def _action_for_update(self, object_type: str, update: Dict,
                           field_prefix: str, candidate_key: Iterable[str]):
        u = self._convert_dates(update)
        f = DataSourceFilter()
        f.and_ = {}
        for key in candidate_key:
            # Don't want key in the upsert as it cannot change anyway
            f.and_[key] = {'eq': {'value': u.pop(key)}}
        u = self._prefix_fields(u, field_prefix)
        u = self._convert_data_objects_in_update_to_dict(u)
        query = self._build_elasticsearch_query(
            object_type,
            object_filters=f)
        return {
            'query': query,
            'script': {
                'source': self._update_script,
                'lang': 'painless',
                'params': {
                    'upsertWith': u
                }
            },
        }

    def __get_index_or_alias(self, object_type: str) -> str:
        return f'{self.index_prefix}-{kebabcase(object_type)}'

    def __get_object_type(self, index: str) -> str:
        start = len(self.index_prefix) + 1
        return snakecase(index[start:])

    def _field_or_keyword(self, object_type: str, name: str):
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

    def get_by_id(
        self,
        object_type: str,
        object_ids: Iterable[DataId],
        **kwargs
    ) -> Iterable[DataObject]:
        f = DataSourceFilter()
        f.and_ = {'_id': {'in_list': {'value': object_ids}}}
        # get_by_id is expected to return objects in the order they were asked for
        # or None if not found, hence the following rearrangement.
        seekable_objects = seekable(self.get_list(object_type, object_filters=f))
        for id_ in object_ids:
            seekable_objects.seek(0)
            for obj in seekable_objects:
                if obj.id == id_:
                    yield obj
                    break
            else:
                yield None

    def get_list_page(
        self,
        object_type: str,
        page: int,
        object_filters: DataSourceFilter = None,
        sort_by: str = None,
        page_size: int = None,
        **kwargs
    ) -> Tuple[Iterable[DataObject], int]:

        resp = self.__get_page_response(
            object_type,
            object_filters,
            sort_by,
            page_size,
            page=page
        )

        return (
            self._convert_dict_to_data_objects(
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
        search_after: list[Any] | None = None
    ) -> dict[str, Any]:

        index = self.__get_index_or_alias(object_type)
        real_index_name = self._get_indices().get(index)
        query = self._build_elasticsearch_query(object_type, object_filters)
        sort = self._build_elasticsearch_sort(object_type, sort_by)
        fields = list(self.runtime_fields[object_type].keys()) \
            if object_type in self.runtime_fields else None
        runtime_mappings = self.runtime_fields[object_type] \
            if object_type in self.runtime_fields else None
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

    def _contains_filter(
        self,
        query: dict[str, Any],
        object_type: str,
        key: str,
        value: str
    ) -> dict[str, Any]:

        search_field = self._field_or_keyword(object_type, key)
        if self.attribute_types[object_type][key] == 'str':
            query['bool']['must'].append(
                {
                    'wildcard': {
                        search_field: {
                            'value': f'{value}*', 'boost': 1.0
                        }
                    }
                }
            )
        else:
            query = self._eq_filter(
                query,
                'must',
                search_field,
                value
            )
        return query

    def _eq_filter(
        self,
        query: dict[str, Any],
        elastic_section: str,
        search_field: str,
        search_value: str
    ) -> dict[str, Any]:

        query['bool'][elastic_section].append({
            'match': {search_field: search_value}
        })

        return query

    def _build_elasticsearch_query(self, object_type: str,
                                   object_filters: DataSourceFilter = None):
        query = {'bool': {'must': [], 'must_not': []}}
        object_filters = self._preprocess_filter(object_type, object_filters)
        # If we want to implement preprocessing of filters, call self._preprocess_filter() here
        if object_filters is None:
            return query
        if object_filters.and_ is not None:
            for k, v in object_filters.and_.items():
                search_field = self._field_or_keyword(object_type, k)
                for op, constraint in v.items():
                    search_value = constraint.get('value')
                    negated = constraint.get('negate', False)
                    elastic_section = 'must_not' if negated else 'must'
                    if 'field' in constraint:
                        other_field = self._field_or_keyword(
                            object_type, constraint['field']
                        )
                        query['bool']['filter'] = \
                            self._get_field_comparison_filter(
                                search_field,
                                other_field,
                                op,
                                negated
                        )
                        continue
                    if op in ['gt', 'gte', 'lt', 'lte']:
                        query['bool'][elastic_section].append({
                            'range': {search_field: {op: search_value}}
                        })
                    if op in ['eq']:
                        query = self._eq_filter(
                            query,
                            elastic_section,
                            search_field,
                            search_value
                        )
                    if op in ['contains']:
                        query['bool'][elastic_section].append({
                            'wildcard': {
                                search_field: {'value': f'{search_value}*', 'boost': 1.0}
                            }
                        })
                    if op in ['exists']:
                        query['bool'][elastic_section].append({
                            'exists': {'field': search_field}
                        })
                    if op in ['in_list']:
                        query['bool'][elastic_section].append({
                            'terms': {search_field: search_value, 'boost': 1.0}
                        })
        return query

    def _get_field_comparison_filter(self, field1: str, field2: str, op: str, negated: bool) -> \
            Dict[str, Dict[str, str]]:
        op_mappings = {
            'eq': '==',
            'lt': '<',
            'lte': '<=',
            'gt': '>',
            'gte': '>='
        }
        negated_mappings = {  # What to return if negated
            True: 'true',
            False: 'false'
        }
        # return {negated_mappings[not negated]}
        return {
            'script': {
                'script': {
                    'source': f"""
                        if (doc[params['field1']].size() > 0
                            && doc[params['field2']].size() > 0) {{
                            if (doc[params['field1']].value.compareTo(doc[params['field2']].value)
                                {op_mappings[op]} 0) {{
                                return {negated_mappings[not negated]}
                            }}
                        }}
                        return {negated_mappings[negated]};
                    """,
                    'params': {
                        'field1': field1,
                        'field2': field2
                    }
                }
            }
        }

    def _build_elasticsearch_sort(
        self,
        object_type: str,
        sort_by: str
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

    def get_list(
        self,
        object_type: str,
        object_filters: DataSourceFilter | None = None,
        session: OperableSession | None = None,
        **kwargs
    ) -> Iterable[DataObject]:
        index = self.__get_index_or_alias(object_type)
        real_index_name = self._get_indices().get(index)
        query = self._build_elasticsearch_query(object_type, object_filters)
        fields = list(self.runtime_fields[object_type].keys()) \
            if object_type in self.runtime_fields else None
        runtime_mappings = self.runtime_fields[object_type] \
            if object_type in self.runtime_fields else None
        generator = self.helpers.scan(self.es,
                                      index=real_index_name,
                                      scroll='10m',
                                      size=500,
                                      query={'query': query},
                                      fields=fields,
                                      runtime_mappings=runtime_mappings)
        return self._convert_dict_to_data_objects(generator)

    def _convert_dict_to_data_objects(self, objs: Dict) -> Iterable:
        for obj in objs:
            if '_source' in obj:
                type_ = self.__real_index_to_object_type(obj['_index'])
                id_ = obj['_id']
                attributes = obj['_source']
                runtime_attributes = obj['fields'] if 'fields' in obj else {}
                yield self._convert_data_dict_to_data_object(
                    type_,
                    id_,
                    attributes,
                    runtime_attributes
                )
            else:
                yield None

    def _convert_data_dict_to_data_object(self, type_, id_, data, runtime_data):
        attributes = {
            k: self.__make_dates(type_, k, v) for k, v in data.items()
            if k in self.attribute_types[type_]
        }
        runtime_attributes = {
            k: self.__make_dates(type_, k, v[0]) for k, v in runtime_data.items()
            if k in self.attribute_types[type_]
        }
        to_one = self.__make_to_one_relations(type_, data)
        return self.data_object_factory(
            type_,
            id_=id_,
            attributes=attributes | runtime_attributes,
            to_one=to_one
        )

    def __make_to_one_relations(
        self,
        type_: str,
        data: dict[str, Any]
    ) -> dict[str, Optional[DataObject]]:

        if type_ not in self.relationship_config:
            return {}

        if self.relationship_config[type_].to_one is None:
            return {}

        return {
            k: self.__make_to_one_relation(data.get(k), v)
            for k, v in self.relationship_config[type_].to_one.items()
        }

    def __make_to_one_relation(
        self,
        relation_data: Optional[dict[str, Any]],
        type_: str
    ) -> Optional[DataObject]:

        if (
            relation_data is None
            or not isinstance(relation_data, Mapping)
        ):
            return None

        id_ = relation_data.get('id')

        if id_ is None:
            return None

        return self._convert_data_dict_to_data_object(
            type_,
            id_,
            relation_data,
            {}  # This can be empty because runtime_fields are not applicable for enriched objects
        )

    def __make_dates(self, object_type, attribute_name, value):
        if self.attribute_types[object_type][attribute_name] == 'datetime' and \
                isinstance(value, str):
            return parser.parse(value)
        return value

    def get_aggregations(
        self,
        object_type: str,
        aggregations: Dict,
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Dict:
        index = self.__get_index_or_alias(object_type)
        real_index_name = self._get_indices().get(index)
        query = self._build_elasticsearch_query(object_type, object_filters)
        fields = list(self.runtime_fields[object_type].keys()) \
            if object_type in self.runtime_fields else None
        runtime_mappings = self.runtime_fields[object_type] \
            if object_type in self.runtime_fields else None
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
        stats_fields: List[str] = [],
        stats: List[str] = [],
        object_filters: DataSourceFilter = None,
        **kwargs
    ):
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
        group_by: List[str],
        stats_fields: List[str] = [],
        stats: List[str] = [],
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> Iterable[dict[Any, int]]:

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
        group_by: List[str],
        stats_fields: List[str] = [],
        stats: List[str] = [],
        after_key: str = None,
        object_filters: DataSourceFilter = None,
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
            stats_fields: List,
            stats: List
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
        object_filters: DataSourceFilter = None,
        **kwargs
    ) -> int:
        index = self.__get_index_or_alias(object_type)
        real_index_name = self._get_indices().get(index)
        query = self._build_elasticsearch_query(object_type, object_filters)
        fields = list(self.runtime_fields[object_type].keys()) \
            if object_type in self.runtime_fields else None
        runtime_mappings = self.runtime_fields[object_type] \
            if object_type in self.runtime_fields else None
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

    def __real_index_to_object_type(self, index: str) -> str:
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
        return type_

    def _get_attribute_types_for_object_type(self, object_type: str) -> Dict:
        index_or_alias_name = self.__get_index_or_alias(object_type)
        real_index_name = self._get_indices().get(index_or_alias_name)
        mapping = self.es.indices.get_mapping(index=index_or_alias_name)
        if 'properties' not in mapping[real_index_name]['mappings']:
            return {}
        properties = mapping[real_index_name]['mappings']['properties']
        standard_types = {
            property_name: self.__map_type(properties[property_name]['type'])
            for property_name in properties
            if 'type' in properties[property_name]
            and property_name != 'uid'
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
        return self.relationship_cfg

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str,
        **kwargs
    ) -> Optional[DataObject]:

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
