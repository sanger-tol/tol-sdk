# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime

from tol.core import core_data_object
from tol.elastic import ElasticDataSource

from .base import DataSourceFixture
from ..services.util import elastic_datasource, get_prefix
from ..types import TEST_OBJECT_TYPES


class ElasticFixture(DataSourceFixture):
    """A `DataSourceFixture` for `ElasticDataSource`"""

    def __init__(self) -> None:
        self.__create_indices()
        self.__upsert_archetypes()

    @property
    def name(self) -> str:
        return 'elastic'

    def get_ds_instance(self) -> ElasticDataSource:
        elastic_ds = elastic_datasource()
        core_data_object(elastic_ds)
        return elastic_ds

    def after_test(self) -> None:
        self.__delete_indices()
        self.__create_indices()
        self.__upsert_archetypes()

    def teardown(self) -> None:
        self.__delete_indices()

    def __get_indices_names(self) -> None:
        prefix = get_prefix()
        return [
            f'{prefix}-{type_}' for type_ in TEST_OBJECT_TYPES
        ]

    def __create_indices(self) -> None:
        """Creates all indices."""

        indices = self.__get_indices_names()
        elastic_ds = self.get_ds_instance()
        elastic_ds.es.indices.create(
            index=indices,
            ignore=[400]
        )

    def __delete_indices(self) -> None:
        """Deletes all indices"""

        indices = self.__get_indices_names()
        elastic_ds = self.get_ds_instance()

        elastic_ds.es.indices.delete(
            index=indices,
            ignore=[400, 404]
        )

    def __upsert_archetypes(self) -> None:
        """
        Ensures that `ElasticDataSource().attribute_types`
        is fully populated by upserting an archetypal
        `DataObject` instance for each.
        We do this directly in ElasticSearch to avoid
        a chicken-and-egg situation
        """

        elastic_ds = self.get_ds_instance()
        elastic_ds.es.index(
            index=get_prefix() + '-root',
            id='#YOLO',
            document={
                'str_column': 'abc',
                'int_column': 42,
                'datetime_column': datetime(2020, 1, 1, 0, 0, 0),
                'bool_column': True,
                'related_object': {'id': '#REL'},
                'list_column': ['item']
            }
        )
        elastic_ds.es.index(
            index=get_prefix() + '-related',
            id='#REL',
            document={
                'str_column': 'abc',
                'int_column': 42,
                'datetime_column': datetime(2020, 1, 1, 0, 0, 0),
                'bool_column': True,
                'list_column': ['item']
            }
        )


elastic = ElasticFixture()
