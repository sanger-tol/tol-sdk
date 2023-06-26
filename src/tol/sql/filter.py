# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, Type

from sqlalchemy.orm import MappedColumn, Query

from .model import Model
from ..core import DataSourceFilter


class DatabaseFilter(ABC):
    """Filters an sqlalchemy.orm Query object"""

    @abstractmethod
    def filter(  # noqa A003
        self,
        query: Query,
        tablename: str,
        model_dict: Dict[str, Type[Model]]
    ) -> Query:
        """Filter the Query object using the given model"""


class DefaultDatabaseFilter(DatabaseFilter):
    """A reasonable-default database filter"""

    # TODO:
    # - relation filters (e.g. specimen.species.taxonid == '9606')
    # - sensible error checking/messages (e.g. if column does not exist)

    def __init__(
        self,
        datasource_filter: Optional[DataSourceFilter]
    ) -> None:

        self.__filter = datasource_filter

    def filter(  # noqa A003
        self,
        query: Query,
        tablename: str,
        model_dict: Dict[str, Type[Model]]
    ) -> Query:

        if self.__filter is None:
            return query

        base_model = model_dict[tablename]
        query = self.__filter_exact(query, base_model)
        query = self.__filter_contains(query, base_model)
        query = self.__filter_in_list(query, base_model)
        query = self.__filter_range(query, base_model)
        return query

    def __filter_exact(self, query: Query, base_model: Type[Model]) -> Query:
        exact_filters = self.__filter.exact
        if exact_filters is None:
            return query
        for k, v in exact_filters.items():
            exact_column = self.__get_column(base_model, k)
            query = query.filter(exact_column == v)
        return query

    def __filter_contains(self, query: Query, base_model: Type[Model]) -> Query:
        contains_filters = self.__filter.contains
        if contains_filters is None:
            return query
        for k, v in contains_filters.items():
            contains_column = self.__get_column(base_model, k)
            term = self.__get_ilike_term(v)
            query = query.filter(contains_column.ilike(term))
        return query

    def __filter_in_list(self, query: Query, base_model: Type[Model]) -> Query:
        in_filters = self.__filter.in_list
        if in_filters is None:
            return query
        for k, v in in_filters.items():
            in_column = self.__get_column(base_model, k)
            query = query.filter(in_column.in_(v))
        return query

    def __filter_range(self, query: Query, base_model: Type[Model]) -> Query:
        range_filters = self.__filter.range
        if range_filters is None:
            return query
        for k, v in range_filters.items():
            range_column = self.__get_column(base_model, k)
            from_, to_ = self.__get_between_term(v)
            query = query.filter(range_column.between(from_, to_))
        return query

    def __get_column(self, model: Type[Model], key: str) -> MappedColumn:
        if key == 'id':
            id_key = model.get_id_column_name()
            return model.get_column(id_key)
        else:
            return model.get_column(key)

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
