# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, List, Type

from .converter import DefaultConverter, TypeFunction
from .database import Database, DefaultDatabase
from .filter import DefaultDatabaseFilter
from .model import Model
from .relationship import DefaultSqlRelationshipConfig
from .session import create_session_factory
from .sort import DefaultDatabaseSorter
from .sql_datasource import (
    ConverterFactory,
    FilterFactory,
    SorterFactory,
    SqlDataSource
)


def __converter_factory(type_function: TypeFunction) -> ConverterFactory:
    return lambda do_factory: DefaultConverter(
        type_function,
        do_factory
    )


def __sorter_factory() -> SorterFactory:
    return lambda sort_term: DefaultDatabaseSorter(
        sort_term
    )


def __filter_factory() -> FilterFactory:
    return lambda ds_filter: DefaultDatabaseFilter(
        ds_filter
    )


def __type_tablename_dict(
    models: List[Type[Model]],
    type_function: TypeFunction
) -> Dict[str, str]:
    """Inverts the TypeFunction callable, using a dictionary"""

    return {
        type_function(m): m.get_table_name() for m in models
    }


def __database(
    models: List[Type[Model]],
    db_uri: str
) -> Database:

    session_factory = create_session_factory(db_uri)
    return DefaultDatabase(session_factory, models)


def create_sql_datasource(
    models: List[Type[Model]],
    db_uri: str,
    type_function: TypeFunction = lambda m: m.get_table_name()
) -> SqlDataSource:
    """
    Creates an SqlDataSource instance using:

    - a list of Model classes
    - a string database URI
    - an (optional) callable that gets the DataObject type for a given Model class
    """

    converter_factory = __converter_factory(type_function)
    sorter_factory = __sorter_factory()
    filter_factory = __filter_factory()
    type_tablename_dict = __type_tablename_dict(models, type_function)
    sql_relationship_config = DefaultSqlRelationshipConfig(models, type_function)
    db = __database(models, db_uri)

    return SqlDataSource(
        db,
        type_tablename_dict,
        sql_relationship_config,
        converter_factory,
        filter_factory,
        sorter_factory
    )
