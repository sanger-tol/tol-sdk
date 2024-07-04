# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from sqlalchemy.orm import MappedColumn, Query

from .model import Model


class DatabaseSorter(ABC):
    """Runs order_by against a query"""

    @abstractmethod
    def sort(
        self,
        query: Query,
        tablename: str,
        model_dict: Dict[str, Type[Model]]
    ) -> Query:
        """Sorts a query using the given models"""


class DefaultDatabaseSorter(DatabaseSorter):

    def __init__(self, sort_term: Optional[str]) -> None:
        if sort_term is None:
            self.__desc = None
            self.__term = None
        elif sort_term.startswith('-'):
            self.__desc = True
            self.__term = sort_term[1:]
        else:
            self.__desc = False
            self.__term = sort_term

    def sort(
        self,
        query: Query,
        tablename: str,
        model_dict: Dict[str, Type[Model]]
    ) -> Query:

        base_model = model_dict[tablename]
        if self.__term is None:
            return self.__apply_default_sort(query, base_model)

        column, query = self.__join_and_get_column(query, base_model, model_dict)
        return self.__apply_default_sort(self.__apply_sort(query, column), base_model)

    def __join_and_get_column(
        self,
        query: Query,
        base_model: type[Model],
        model_dict: Dict[str, Type[Model]]
    ) -> tuple[MappedColumn, Query]:

        model = base_model

        relations = self.__term.split('.')[:-1]
        for relation in relations:
            column = getattr(model, relation)
            query = query.join(column)
            to_one = model.get_to_one_relationship_config()
            model = model_dict[
                to_one[relation]
            ]

        column = self.__get_column(
            model,
            self.__term.split('.')[-1]
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

    def __apply_default_sort(self, query: Query, model: Type[Model]):
        if self.__term != 'id':
            # Add a default sort by id after the other sort
            id_key = model.get_id_column_name()
            id_column = model.get_column(id_key)
            return query.order_by(id_column)
        return query
