# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from sqlalchemy.orm import MappedColumn, Query

from .filter import DatabaseFilter
from .model import Model


class DatabaseSorter(ABC):
    """Runs order_by against a query"""

    @abstractmethod
    def sort(
        self,
        query: Query,
        tablename: str,
        model_dict: Dict[str, Type[Model]],
        filters: DatabaseFilter,
    ) -> Query:
        """Sorts a query using the given models"""


class DefaultDatabaseSorter(DatabaseSorter):

    def __init__(self, sort_term: Optional[str]) -> None:
        if sort_term is None:
            self.__desc = False
            self.term = 'id'
        elif sort_term.startswith('-'):
            self.__desc = True
            self.term = sort_term[1:]
        else:
            self.__desc = False
            self.term = sort_term

    def sort(
        self,
        query: Query,
        tablename: str,
        model_dict: Dict[str, Type[Model]],
        filters: DatabaseFilter | None = None,
    ) -> Query:

        if filters is not None:
            column = filters.get_column(self.term)
        else:
            column, query = self.__join_and_get_column(
                query,
                model_dict[tablename],
                model_dict,
            )
        return self.__apply_sort(query, column)

    def __join_and_get_column(
        self,
        query: Query,
        base_model: type[Model],
        model_dict: Dict[str, Type[Model]]
    ) -> tuple[MappedColumn, Query]:

        model = base_model

        relations = self.term.split('.')[:-1]
        for relation in relations:
            column = getattr(model, relation)
            query = query.join(column)
            to_one = model.get_to_one_relationship_config()
            model = model_dict[
                to_one[relation]
            ]

        column = self.__get_column(
            model,
            self.term.split('.')[-1]
        )

        return column, query

    def __get_column(self, model: Type[Model], term: str) -> MappedColumn:
        if term == 'id':
            id_key = model.get_id_column_name()
            return model.get_column(id_key)
        else:
            return model.get_column(term)

    def __apply_sort(self, query: Query, column: MappedColumn) -> Query:
        if self.__desc:
            return query.order_by(column.desc())
        else:
            return query.order_by(column)
