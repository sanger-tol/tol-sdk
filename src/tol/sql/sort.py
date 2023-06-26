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

        if self.__term is None:
            return query

        model = model_dict[tablename]
        column = self.__get_column(model)
        return self.__apply_sort(query, column)

    def __get_column(self, model: Type[Model]) -> MappedColumn:
        if self.__term == 'id':
            id_key = model.get_id_column_name()
            return model.get_column(id_key)
        else:
            return model.get_column(self.__term)

    def __apply_sort(self, query: Query, column: MappedColumn) -> Query:
        if self.__desc:
            return query.order_by(column.desc())
        else:
            return query.order_by(column)
