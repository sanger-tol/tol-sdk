# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import MutableMapping
from functools import reduce
from itertools import chain
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple, Type

from sqlalchemy import BinaryExpression, cast, inspect, not_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import MappedColumn, Query, Session, aliased
from sqlalchemy.orm.util import AliasedClass

from .model import Model
from ..core import DataSourceFilter


class AliasTrie(MutableMapping[str, 'AliasTrie']):

    def __init__(self, alias: AliasedClass[Model]) -> None:
        self.__alias = alias
        self.__dict: dict[str, AliasTrie] = {}

    @property
    def alias(self) -> AliasedClass[Model]:
        return self.__alias

    def __getitem__(self, k: str) -> AliasTrie:
        return self.__dict[k]

    def __setitem__(self, key: str, value: AliasTrie) -> None:
        self.__dict[key] = value

    def __delitem__(self, key: str) -> None:
        raise NotImplementedError()

    def __iter__(self) -> Iterator[str]:
        return iter(self.__dict)

    def __len__(self) -> int:
        return len(self.__dict)


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
    def get_column(self, key: str) -> MappedColumn:
        """Gets the column for the given `DataObject` key"""

    @abstractmethod
    def add_field(self, field: str) -> None:
        """Adds a relation field to the filter, for joining later"""

    @abstractmethod
    def get_query(self, session: Session, base_model: type[Model]) -> Query[Model]:
        """Gets an aliased query"""


class DefaultDatabaseFilter(DatabaseFilter):
    """A reasonable-default database filter"""

    # TODO:
    # - sensible error checking/messages (e.g. if column does not exist)

    def __init__(
        self,
        datasource_filter: Optional[DataSourceFilter]
    ) -> None:

        self.__filter = datasource_filter
        self.__rel_keys: set[str] = set()

    def filter(  # noqa A003
        self,
        query: Query[Model],
        __tablename: str,
        __model_dict: Dict[str, Type[Model]]
    ) -> Query[Model]:

        self.__rel_keys.update(
            self.__generate_relational_keys()
        )

        self.__alias_trie = self.__build_alias_trie(
            self.__rel_keys,
        )

        query = self.__apply_joins(
            query,
            self.__alias_trie,
            self.__base_alias,
        )

        if self.__filter is None:
            return query

        query = self.__filter_top_and_(query)
        query = self.__filter_top_exact(query)
        query = self.__filter_top_contains(query)
        query = self.__filter_top_in_list(query)
        query = self.__filter_top_range(query)

        return query

    def get_query(self, session: Session, base_model: Model) -> Query[Model]:
        # TODO this is not thread safe
        self.__base_alias: AliasedClass[Model] = aliased(
            base_model,
        )

        return session.query(self.__base_alias)

    def __apply_joins(
        self,
        query: Query[Model],
        parent_trie: AliasTrie,
        parent_alias: AliasedClass[Model],
    ) -> Query[Model]:

        for part, trie in parent_trie.items():
            alias = trie.alias

            query = query.join(alias, getattr(parent_alias, part))

            query = self.__apply_joins(
                query,
                trie,
                alias,
            )

        return query

    def __create_alias(
        self,
        parent_alias: AliasedClass[Model],
        relationship_name: str,
    ) -> AliasedClass[Model]:

        mapper = inspect(parent_alias).mapper
        rel_prop = mapper.relationships[relationship_name]
        target_model = rel_prop.mapper.class_
        return aliased(target_model)

    def add_field(self, field: str) -> None:
        self.__rel_keys.add(field)

    def __build_alias_trie(self, paths: Iterable[str]) -> AliasTrie:
        trie = AliasTrie(self.__base_alias)

        for path in paths:
            parts = path.split('.')
            current_alias = self.__base_alias
            current = trie
            for part in parts[:-1]:
                if part not in current:
                    step = AliasTrie(
                        self.__create_alias(
                            current_alias,
                            part,
                        )
                    )
                    current[part] = step
                    current = step
                current_alias = current.alias

        return trie

    def __generate_relational_keys(self) -> Iterator[str]:
        if not self.__filter:
            return []

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
                self.get_column(column_key),
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
            column = self.get_column(field)
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
        return column.type.python_type is str

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
            exact_column = self.get_column(k)
            query = query.filter(exact_column == v)
        return query

    def __filter_top_contains(self, query: Query[Model]) -> Query[Model]:
        contains_filters = self.__filter.contains
        if contains_filters is None:
            return query
        for k, v in contains_filters.items():
            contains_column = self.get_column(k)
            term = self.__get_ilike_term(v)
            query = query.filter(contains_column.ilike(term))
        return query

    def __filter_top_in_list(self, query: Query[Model]) -> Query[Model]:
        in_filters = self.__filter.in_list
        if in_filters is None:
            return query
        for k, v in in_filters.items():
            in_column = self.get_column(k)
            query = query.filter(in_column.in_(v))
        return query

    def __filter_top_range(self, query: Query[Model]) -> Query[Model]:
        range_filters = self.__filter.range
        if range_filters is None:
            return query
        for k, v in range_filters.items():
            range_column = self.get_column(k)
            from_, to_ = self.__get_between_term(v)
            query = query.filter(range_column.between(from_, to_))
        return query

    def get_column(self, key: str, model: type[Any] | None = None) -> MappedColumn:
        model = self.__alias_trie.alias if model is None else model
        if key == 'id':
            return self.__get_id_column(model)
        elif '.' in key:
            return self.__get_relation_column(key)
        else:
            return self.__get_column_attr(model, key)

    def __get_id_column(self, model: type[Model]) -> MappedColumn:
        og_model: type[Model] = model._aliased_insp.mapper.class_
        id_key = og_model.get_id_column_name()
        return self.__get_column_attr(model, id_key)

    def __get_column_attr(self, model: AliasedClass[Model], key: str) -> MappedColumn:
        columns = {
            col.key: col
            for col in model._aliased_insp.selectable.c
        }
        return columns[key]

    def __get_relation_column(
        self,
        key: str
    ) -> MappedColumn:

        (*initial, column) = key.split('.')

        if not initial:
            return self.get_column(key)

        trie = self.__alias_trie
        for i in initial:
            trie = trie[i]

        return self.get_column(
            column,
            model=trie.alias,
        )

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
