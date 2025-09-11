# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable, Dict, List, Type

from .database import Database, DefaultDatabase
from .filter import DefaultDatabaseFilter
from .model import Model
from .relationship import DefaultSqlRelationshipConfig
from .session import create_session_factory
from .sort import DefaultDatabaseSorter
from .sql_converter import DefaultDataObjectConverter, DefaultModelConverter, TypeFunction
from .sql_datasource import (
    BackConverterFactory,
    ConverterFactory,
    FilterFactory,
    SorterFactory,
    SqlDataSource
)
from ..api_base.misc.auth_context import default_ctx_getter


DatabaseFactory = Callable[
    [List[Type[Model]], str],
    Database
]


def __model_converter_factory(
    type_function: TypeFunction
) -> ConverterFactory:

    return lambda do_factory, requested_fields: DefaultModelConverter(
        type_function,
        do_factory,
        requested_fields=requested_fields
    )


def __back_converter_factory(
    models: List[Type[Model]],
    type_function: TypeFunction
) -> BackConverterFactory:

    models_dict = {
        type_function(m): m for m in models
    }
    return lambda: DefaultDataObjectConverter(
        models_dict
    )


def __sorter_factory() -> SorterFactory:
    return lambda sort_term: DefaultDatabaseSorter(
        sort_term
    )


def __type_tablename_dict(
    models: List[Type[Model]],
    type_function: TypeFunction
) -> Dict[str, str]:
    """Inverts the TypeFunction callable, using a dictionary"""

    return {
        type_function(m): m.get_table_name() for m in models
    }


def __filter_factory() -> FilterFactory:

    return lambda ds_filter: DefaultDatabaseFilter(
        ds_filter,
    )


def __database(
    models: List[Type[Model]],
    db_uri: str
) -> Database:

    session_factory = create_session_factory(db_uri)
    return DefaultDatabase(session_factory, models)


def create_sql_datasource(
    models: List[Type[Model]],
    db_uri: str,
    behind_api: bool = False,

    # arguments below are optional and used mainly for testing
    type_function: TypeFunction = lambda m: m.get_table_name(),
    api_user_id_getter: Callable[[], str] = lambda: default_ctx_getter().user_id,
    database_factory: DatabaseFactory = __database,
    model_factory: BackConverterFactory = __back_converter_factory,
    do_factory: ConverterFactory = __model_converter_factory
) -> SqlDataSource:
    """
    Creates an SqlDataSource instance using:

    - a list of Model classes
    - a string database URI
    - an (optional) callable that gets the DataObject type for a given Model class
    """

    converter_factory = do_factory(type_function)
    back_converter_factory = model_factory(models, type_function)
    sorter_factory = __sorter_factory()
    type_tablename_dict = __type_tablename_dict(models, type_function)
    sql_relationship_config = DefaultSqlRelationshipConfig(models, type_function)
    filter_factory = __filter_factory()
    db = database_factory(models, db_uri)

    user_id_getter = api_user_id_getter if behind_api else None

    return SqlDataSource(
        db,
        type_tablename_dict,
        sql_relationship_config,
        converter_factory,
        back_converter_factory,
        filter_factory,
        sorter_factory,
        user_id_getter=user_id_getter
    )
