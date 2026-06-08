# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from collections.abc import Callable
from typing import Any

from ..core import DataSourceFilter, DataSourceFilterConverter
from ..core.filter_strategy import FilterStrategy

# Import only for typing due to circular imports
if typing.TYPE_CHECKING:
    from .elastic_datasource import ElasticDataSource


class ElasticFilterStrategy(FilterStrategy[dict]):
    """Converts a DataSourceFilter to an Elasticsearch bool query dict."""

    def __init__(self, field_resolver: Callable[[str, str], str]) -> None:
        self._field_resolver = field_resolver

    def convert(self, object_type, object_filters=None):
        query = {'bool': {'must': [], 'must_not': []}}
        if object_filters is None:
            return query
        if object_filters.and_ is not None:
            for k, v in object_filters.and_.items():
                search_field = self._field_resolver(object_type, k)
                for op, constraint in v.items():
                    search_value = constraint.get('value')
                    negated = constraint.get('negate', False)
                    elastic_section = 'must_not' if negated else 'must'
                    if 'field' in constraint:
                        other_field = self._field_resolver(
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
            dict[str, dict[str, str]]:
        op_mappings = {
            'eq': '==',
            'lt': '<',
            'lte': '<=',
            'gt': '>',
            'gte': '>='
        }
        negated_mappings = {
            True: 'true',
            False: 'false'
        }
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


class ElasticFilterConverter(DataSourceFilterConverter):
    """Backward-compatible wrapper that delegates to ElasticFilterStrategy."""

    __slots__ = ['__elastic_datasource', '__strategy']
    __elastic_datasource: ElasticDataSource

    def __init__(self, elastic_datasource: ElasticDataSource) -> None:
        super().__init__()
        self.__elastic_datasource = elastic_datasource
        self.__strategy = ElasticFilterStrategy(elastic_datasource._field_or_keyword)

    def convert(self, object_type: str, object_filters: DataSourceFilter | None = None) -> dict:
        object_filters = self.__elastic_datasource._preprocess_filter(object_type, object_filters)
        return self.__strategy.convert(object_type, object_filters)
