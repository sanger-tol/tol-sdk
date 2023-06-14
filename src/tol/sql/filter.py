# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from sqlalchemy.orm import Query

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

        # TODO - implement the other filter types
        base_model = model_dict[tablename]
        query = self.__filter_exact(query, base_model)
        return query

    def __filter_exact(self, query: Query, base_model: Type[Model]) -> Query:
        exact_filters = self.__filter.exact
        if exact_filters is None:
            return query
        for k, v in exact_filters.items():
            query = query.filter(getattr(base_model, k) == v)
        return query
