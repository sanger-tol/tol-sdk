# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any
from unittest.mock import create_autospec

import pytest

from tol.core import (
    DataObject,
    core_data_object
)
from tol.core.relationship import (
    RelationshipConfig
)
from tol.sql import SqlDataSource
from tol.sql.database import Database
from tol.sql.filter import DatabaseFilter
from tol.sql.model import Model
from tol.sql.relationship import (
    SqlRelationshipConfig
)
from tol.sql.sort import DatabaseSorter
from tol.sql.sql_converter import (
    DataObjectConverter,
    DefaultModelConverter,
    ModelConverter
)


@pytest.fixture(scope='function')
def db() -> Database:
    mock_db = create_autospec(
        Database,
        spec_set=True
    )
    mock_db.attribute_types = {
        'r1': {},
        'r2': {
            'str_column': str
        }
    }

    return mock_db


@pytest.fixture(scope='module')
def type_tablename_map() -> dict[str, str]:
    return {
        'r1': 'r1',
        'r2': 'r2'
    }


@pytest.fixture(scope='module')
def rel_config(
) -> SqlRelationshipConfig:

    config = create_autospec(
        SqlRelationshipConfig,
        spect_set=True
    )
    config.to_dict.return_value = {
        'r1': RelationshipConfig(
            to_one={'r2_d2': 'r2'}
        )
    }

    return config


@pytest.fixture(scope='function')
def do_converter() -> DataObjectConverter:
    return create_autospec(
        DataObjectConverter,
        spec_set=True
    )


@pytest.fixture(scope='function')
def model_converter() -> ModelConverter:
    return create_autospec(
        ModelConverter,
        spec_set=True
    )


@pytest.fixture(scope='function')
def db_filter() -> DatabaseFilter:
    return create_autospec(
        DatabaseFilter,
        spec_set=True
    )


@pytest.fixture(scope='function')
def db_sorter() -> DatabaseSorter:
    return create_autospec(
        DatabaseSorter,
        spec_set=True
    )


@pytest.fixture(scope='function')
def sql_ds(
    db: Database,
    type_tablename_map: dict[str, str],
    rel_config: SqlRelationshipConfig,
    do_converter: DataObjectConverter,
    model_converter: ModelConverter,
    db_filter: DatabaseFilter,
    db_sorter: DatabaseSorter
) -> SqlDataSource:

    ds = SqlDataSource(
        db,
        type_tablename_map,
        rel_config,
        lambda _: model_converter,
        lambda: do_converter,
        lambda: db_filter,
        lambda: db_sorter
    )
    core_data_object(ds)

    # prevent chicken-and-the-egg
    model_converter_override = DefaultModelConverter(
        lambda t: t.get_table_name(),
        ds.data_object_factory
    )
    model_converter.convert_iterable.side_effect = (
        model_converter_override.convert_iterable
    )

    return ds


class TestFetch:
    """No superfluous fetches"""

    def test_relation(
        self,
        sql_ds: SqlDataSource,
        db: Database,
        model_converter: ModelConverter
    ):
        """
        Converter returns objects with relationships
        -> no relation fetch occurs.
        """

        mock_r2 = self.__mock_model(
            'r2',
            attributes={
                'str_column': 'lol'
            }
        )

        mock_r1 = self.__mock_model(
            'r1',
            to_ones={
                'r2_d2': mock_r2
            }
        )

        db.get_by_id.return_value = mock_r1

        fetched_r1 = sql_ds.get_one(
            'r1',
            'does not matter'
        )
        db.get_by_id.assert_called_once()
        db.get_to_one_relation.assert_not_called()

        fetched_r2 = fetched_r1.r2_d2
        assert fetched_r2 is not None
        db.get_by_id.assert_called_once()
        db.get_to_one_relation.assert_not_called()

        assert fetched_r2.str_column == 'lol'
        db.get_by_id.assert_called_once()
        db.get_to_one_relation.assert_not_called()

    def __mock_model(
        self,
        tablename: str,
        id_: str | None = None,
        attributes: dict[str, Any] = {},
        to_ones: dict[str, Model] = {}
    ) -> Model:

        mock_model = create_autospec(
            Model,
            spec_set=True
        )

        mock_model.get_table_name.return_value = tablename
        mock_model.instance_id = id_
        mock_model.instance_attributes = attributes
        mock_model.instance_to_one_relations = to_ones

        return mock_model

