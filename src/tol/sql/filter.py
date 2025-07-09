# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import reduce
from itertools import chain
from typing import Any, Dict, Iterator, Optional, Tuple, Type

from sqlalchemy import BinaryExpression, cast, not_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import MappedColumn, Query

from .model import Model
from .relationship import SqlRelationshipConfig
from ..core import DataSourceFilter


class DatabaseFilter(ABC):
    """Filters an `sqlalchemy.orm` `Query` object"""

    @abstractmethod
    def filter(  # noqa A003
        self,
        query: Query,
        tablename: str,
        model_dict: Dict[str, Type[Model]]
    ) -> Query:
        """Filter the Query object using the given model"""

    @abstractmethod
    def get_column(self, model: Type[Model], key: str) -> MappedColumn:
        """Gets the column for the given `DataObject` key"""

    @abstractmethod
    def apply_joins_on_query(
        self,
        query: Query,
        join_columns: list[MappedColumn]
    ) -> Query:
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
        query: Query,
        tablename: str,
        model_dict: Dict[str, Type[Model]]
    ) -> Query:

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
        query: Query
    ) -> Query:

        return reduce(
            lambda q, jc: self.apply_joins_on_query(
                q,
                jc
            ),
            self.__get_join_columns_lists(),
            query
        )

    def apply_joins_on_query(
        self,
        query: Query,
        join_columns: list[MappedColumn]
    ) -> Query:

        return reduce(
            lambda q, c: q.join(c),
            join_columns,
            query
        )

    def __get_join_columns_lists(self) -> Iterator[list[MappedColumn]]:
        base_tablename = self.__base_model.get_table_name()

        return (
            list(
                self.__generate_join_columns(
                    base_tablename,
                    k
                )
            )
            for k in self.__generate_relational_keys()
        )

    def __generate_join_columns(
        self,
        base_tablename: str,
        relational_key: str
    ) -> Iterator[MappedColumn]:

        k_split = relational_key.split('.')
        mid_tablename = base_tablename
        mid_type = self.__inverted_dict[mid_tablename]

        for next_ in k_split[:-1]:
            mid_model = self.__model_dict[mid_tablename]
            yield getattr(mid_model, next_)
            mid_type = self.__r_dict[mid_type].to_one[next_]
            mid_tablename = self.__type_tablename_dict[mid_type]

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

    def __filter_top_and_(self, query: Query) -> Query:
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
        query: Query,
        column_key: str,
        term_dict: dict[str, dict[str, Any]]
    ) -> Query:

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
        query: Query,
        column: MappedColumn,
        op: str,
        term: dict[str, dict[str, Any]]
    ) -> Query:

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
        query: Query,
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query:

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
        query: Query,
        expression: BinaryExpression,
        column: MappedColumn,
        negate: bool
    ) -> Query:

        if negate is True:
            return query.filter(
                (column.is_(None)) | not_(expression)
            )
        else:
            return query.filter(expression)

    def __filter_in_list(
        self,
        query: Query,
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query:

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
        query: Query,
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query:

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
        query: Query,
        column: MappedColumn,
        value: str,
        negate: bool
    ) -> Query:

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
        query: Query,
        column: MappedColumn,
        value: Any,
        negate: bool
    ) -> Query:

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
        query: Query,
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query:

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
        query: Query,
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query:

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
        query: Query,
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query:

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
        query: Query,
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query:

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
        query: Query,
        column: MappedColumn,
        term: dict[str, Any]
    ) -> Query:

        value, negate = self.__parse_value_negate(term)
        expression = column >= value

        return self.__negatable_filter(
            query,
            expression,
            column,
            negate
        )

    def __filter_top_exact(self, query: Query) -> Query:
        exact_filters = self.__filter.exact
        if exact_filters is None:
            return query
        for k, v in exact_filters.items():
            exact_column = self.get_column(self.__base_model, k)
            query = query.filter(exact_column == v)
        return query

    def __filter_top_contains(self, query: Query) -> Query:
        contains_filters = self.__filter.contains
        if contains_filters is None:
            return query
        for k, v in contains_filters.items():
            contains_column = self.get_column(self.__base_model, k)
            term = self.__get_ilike_term(v)
            query = query.filter(contains_column.ilike(term))
        return query

    def __filter_top_in_list(self, query: Query) -> Query:
        in_filters = self.__filter.in_list
        if in_filters is None:
            return query
        for k, v in in_filters.items():
            in_column = self.get_column(self.__base_model, k)
            query = query.filter(in_column.in_(v))
        return query

    def __filter_top_range(self, query: Query) -> Query:
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
            return model.get_column(key)

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
        end_model = self.__model_dict[end_tablename]
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
