# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import reduce
from itertools import chain
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple, Type

from sqlalchemy import BinaryExpression, cast, not_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import MappedColumn, Query, aliased
from sqlalchemy.orm.properties import RelationshipProperty
from sqlalchemy.orm.util import AliasedClass

from .model import Model
from .relationship import SqlRelationshipConfig
from ..core import DataSourceFilter


JoinTrie = dict[str, 'JoinTrie']
"""A prefix tree, for aliasing relationship attribute traversal"""


class DatabaseFilter(ABC):
    """Filters an `sqlalchemy.orm` `Query` object"""

    @abstractmethod
    def filter(  # noqa A003
        self,
        query: Query[Model],
        tablename: str,
        model_dict: Dict[str, Type[Model]]
    ) -> Query[Model]:
        """Filter the Query object using the given model"""

    @abstractmethod
    def get_column(self, model: Type[Model], key: str) -> MappedColumn:
        """Gets the column for the given `DataObject` key"""

    @abstractmethod
    def apply_joins_on_query(
        self,
        query: Query[Model],
        join_columns: list[MappedColumn]
    ) -> Query[Model]:
        """Applys necessary joins on relation columns"""


class DefaultDatabaseFilter(DatabaseFilter):
    """A reasonable-default database filter"""

    # TODO:
    # - sensible error checking/messages (e.g. if column does not exist)

    def __init__(
        self,
        datasource_filter: Optional[DataSourceFilter],
        type_tablename_dict: dict[str, str],
        relationship_config: SqlRelationshipConfig
    ) -> None:

        self.__filter = datasource_filter
        self.__type_tablename_dict = type_tablename_dict
        self.__r_dict = relationship_config.to_dict()
        self.__inverted_dict = {
            v: k for k, v in type_tablename_dict.items()
        }

    def filter(  # noqa A003
        self,
        query: Query[Model],
        tablename: str,
        model_dict: Dict[str, Type[Model]]
    ) -> Query[Model]:

        if self.__filter is None:
            return query

        # TODO this is not thread safe
        self.__base_model = model_dict[tablename]
        self.__model_dict = model_dict

        query = self.__join_on_relations(query)

        query = self.__filter_top_and_(query)
        query = self.__filter_top_exact(query)
        query = self.__filter_top_contains(query)
        query = self.__filter_top_in_list(query)
        query = self.__filter_top_range(query)

        return query

    def __join_on_relations(
        self,
        query: Query[Model]
    ) -> Query[Model]:

        relational_keys = self.__generate_relational_keys()
        join_trie = self.__build_join_trie(relational_keys)
        aliases = self.__build_aliases(
            self.__base_model,
            join_trie,
            (),
        )

        for path, alias in aliases.items():
            current_model = self.__base_model
            current_path: list[str] = []
            for step in path:
                current_path.append(step)
                parent_alias = aliases.get(tuple(current_path[:-1]), current_model)
                query = query.join(alias, getattr(parent_alias, step))

        return query

    def apply_joins_on_query(
        self,
        query: Query[Model],
        join_columns: list[MappedColumn]
    ) -> Query[Model]:

        return reduce(
            self.__apply_join_on_query,
            join_columns,
            query
        )

    def __build_join_trie(self, paths: Iterable[str]) -> JoinTrie:
        trie: JoinTrie = {}

        for path in paths:
            parts = path.split('.')
            current = trie
            for part in parts:
                current = current.setdefault(part, {})

        return trie

    def __build_aliases(
        self,
        model: type[Model],
        trie: JoinTrie,
        path: tuple[str, ...],
    ) -> dict[tuple[str, ...], type[AliasedClass[Model]]]:

        aliases: dict[tuple[str, ...], type[AliasedClass[Model]]] = {}

        for rel_name, subtree in trie.items():
            attr = getattr(model, rel_name)
            current_path = path + (rel_name,)

            if not hasattr(attr, 'property'):
                continue

            if not isinstance(attr.property, RelationshipProperty):
                continue

            alias = aliased(attr.property.mapper.class_)
            aliases[current_path] = alias

            if subtree:
                child_aliases = self.__build_aliases(alias, subtree, current_path)
                aliases.update(child_aliases)

        return aliases

    def __generate_relational_keys(self) -> Iterator[str]:
        chained = chain(
            self.__none_coalesce(self.__filter.exact),
            self.__none_coalesce(self.__filter.contains),
            self.__none_coalesce(self.__filter.in_list),
            self.__none_coalesce(self.__filter.range),
            self.__none_coalesce(self.__filter.and_),
            self.__filter_pointer_targets
        )
        return (
            k for k in chained
            if '.' in k
        )

    @property
    def __filter_pointer_targets(self) -> Iterator[str]:
        not_none = self.__none_coalesce(self.__filter.and_)
        for column_body in not_none.values():
            for term in column_body.values():
                if 'field' in term:
                    yield term['field']

    def __none_coalesce(self, in_: Optional[dict]) -> dict:
        return in_ if in_ is not None else {}

    def __filter_top_and_(self, query: Query[Model]) -> Query[Model]:
        if not self.__filter.and_:
            return query

        return reduce(
            lambda q, kv: self.__switch_and_term_dict(
                q,
                *kv
            ),
            self.__filter.and_.items(),
            query
        )

    def __switch_and_term_dict(
        self,
        query: Query[Model],
        column_key: str,
        term_dict: dict[str, dict[str, Any]]
    ) -> Query[Model]:

        return reduce(
            lambda q, kv: self.__switch_and_term(
                q,
                self.get_column(self.__base_model, column_key),
                *kv
            ),
            term_dict.items(),
            query
        )

    def __switch_and_term(
        self,
        query: Query[Model],
        column: MappedColumn,
        op: str,
        term: dict[str, dict[str, Any]]
    ) -> Query[Model]:

        filter_dict = defaultdict(
            lambda: lambda *_: query,
            eq=self.__filter_eq,
            contains=self.__filter_contains,
            in_list=self.__filter_in_list,
            gt=self.__filter_gt,
            gte=self.__filter_gte,
            lt=self.__filter_lt,
            lte=self.__filter_lte,
            exists=self.__filter_exists
        )

        return filter_dict[op](query, column, term)

    def __parse_value_negate(
        self,
        term: dict[str, Any]
    ) -> tuple[Any, bool]:

        negate = term.get('negate', False)

        if 'field' in term:
            field = term['field']
            column = self.get_column(
                self.__base_model,
                field
            )
            return column, negate
        else:
            return term.get('value'), negate

    def __filter_exists(
        self,
        query: Query[Model],
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query[Model]:

        _, negate = self.__parse_value_negate(term)

        if negate:
            return query.filter(
                column.is_(None)
            )
        else:
            return query.filter(
                column.is_not(None)
            )

    def __negatable_filter(
        self,
        query: Query[Model],
        expression: BinaryExpression,
        column: MappedColumn,
        negate: bool
    ) -> Query[Model]:

        if negate is True:
            return query.filter(
                (column.is_(None)) | not_(expression)
            )
        else:
            return query.filter(expression)

    def __filter_in_list(
        self,
        query: Query[Model],
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query[Model]:

        value, negate = self.__parse_value_negate(term)
        expression = column.in_(value)

        return self.__negatable_filter(
            query,
            expression,
            column,
            negate
        )

    def __filter_contains(
        self,
        query: Query[Model],
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query[Model]:

        value, negate = self.__parse_value_negate(term)

        if self.__column_is_str(column):
            return self.__filter_contains_str(
                query,
                column,
                value,
                negate
            )
        else:
            return self.__filter_contains_list(
                query,
                column,
                value,
                negate
            )

    def __column_is_str(self, column: MappedColumn) -> bool:
        return column.type.python_type == str

    def __filter_contains_str(
        self,
        query: Query[Model],
        column: MappedColumn,
        value: str,
        negate: bool
    ) -> Query[Model]:

        ilike = self.__get_ilike_term(value)
        expression = column.ilike(ilike)

        return self.__negatable_filter(
            query,
            expression,
            column,
            negate
        )

    def __filter_contains_list(
        self,
        query: Query[Model],
        column: MappedColumn,
        value: Any,
        negate: bool
    ) -> Query[Model]:

        jsonb_column = cast(column, JSONB)
        expression = jsonb_column.op('@>')([value])

        return self.__negatable_filter(
            query,
            expression,
            column,
            negate
        )

    def __filter_eq(
        self,
        query: Query[Model],
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query[Model]:

        value, negate = self.__parse_value_negate(term)
        expression = column == value

        return self.__negatable_filter(
            query,
            expression,
            column,
            negate
        )

    def __filter_lt(
        self,
        query: Query[Model],
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query[Model]:

        value, negate = self.__parse_value_negate(term)
        expression = column < value

        return self.__negatable_filter(
            query,
            expression,
            column,
            negate
        )

    def __filter_lte(
        self,
        query: Query[Model],
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query[Model]:

        value, negate = self.__parse_value_negate(term)
        expression = column <= value

        return self.__negatable_filter(
            query,
            expression,
            column,
            negate
        )

    def __filter_gt(
        self,
        query: Query[Model],
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query[Model]:

        value, negate = self.__parse_value_negate(term)
        expression = column > value

        return self.__negatable_filter(
            query,
            expression,
            column,
            negate
        )

    def __filter_gte(
        self,
        query: Query[Model],
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query[Model]:

        value, negate = self.__parse_value_negate(term)
        expression = column >= value

        return self.__negatable_filter(
            query,
            expression,
            column,
            negate
        )

    def __filter_top_exact(self, query: Query[Model]) -> Query[Model]:
        exact_filters = self.__filter.exact
        if exact_filters is None:
            return query
        for k, v in exact_filters.items():
            exact_column = self.get_column(self.__base_model, k)
            query = query.filter(exact_column == v)
        return query

    def __filter_top_contains(self, query: Query[Model]) -> Query[Model]:
        contains_filters = self.__filter.contains
        if contains_filters is None:
            return query
        for k, v in contains_filters.items():
            contains_column = self.get_column(self.__base_model, k)
            term = self.__get_ilike_term(v)
            query = query.filter(contains_column.ilike(term))
        return query

    def __filter_top_in_list(self, query: Query[Model]) -> Query[Model]:
        in_filters = self.__filter.in_list
        if in_filters is None:
            return query
        for k, v in in_filters.items():
            in_column = self.get_column(self.__base_model, k)
            query = query.filter(in_column.in_(v))
        return query

    def __filter_top_range(self, query: Query[Model]) -> Query[Model]:
        range_filters = self.__filter.range
        if range_filters is None:
            return query
        for k, v in range_filters.items():
            range_column = self.get_column(self.__base_model, k)
            from_, to_ = self.__get_between_term(v)
            query = query.filter(range_column.between(from_, to_))
        return query

    def get_column(self, model: Type[Model], key: str) -> MappedColumn:
        if key == 'id':
            return self.__get_id_column(model)
        elif '.' in key:
            return self.__get_relation_column(model, key)
        else:
            return getattr(model, key)

    def __get_id_column(self, model: type[Model]) -> MappedColumn:
        id_key = model.get_id_column_name()
        return model.get_column(id_key)

    def __get_relation_column(
        self,
        model: Type[Model],
        key: str
    ) -> MappedColumn:

        split_keys = key.split('.')

        base_tablename = model.get_table_name()
        mid_type = self.__inverted_dict[base_tablename]

        for split_ in split_keys[:-1]:
            mid_type = self.__r_dict[mid_type].to_one[split_]

        end_tablename = self.__type_tablename_dict[mid_type]
        end_model = aliased(self.__model_dict[end_tablename])
        end_key = split_keys[-1]

        return self.get_column(end_model, end_key)

    def __get_ilike_term(self, value: str) -> str:
        escaped = self.__escape_ilike(value)
        return f'%{escaped}%'

    def __get_between_term(self, value: Dict[str, Any]) -> Tuple[Any, Any]:
        from_ = value['from']
        to_ = value['to']
        return from_, to_

    def __escape_ilike(self, value: str) -> str:
        return (
            value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        )
