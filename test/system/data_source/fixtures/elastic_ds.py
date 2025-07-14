# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import time

from tol.core import core_data_object
from tol.elastic import ElasticDataSource

from .base import DataSourceFixture
from ..services.util import (
    create_indices,
    delete_indices,
    elastic_datasource,
    upsert_archetypes,
    wait_for_ready,
    get_prefix,
)


class ElasticFixture(DataSourceFixture):
    """A `DataSourceFixture` for `ElasticDataSource`"""

    def __init__(
        self,
        prefix: str,
    ) -> None:

        self.__prefix = prefix
        wait_for_ready()

    @property
    def name(self) -> str:
        return 'elastic'

    def get_ds_instance(self) -> ElasticDataSource:
        elastic_ds = elastic_datasource(self.__prefix)
        core_data_object(elastic_ds)
        return elastic_ds

    def after_test(self) -> None:
        delete_indices(self.__prefix)

    def before_test(self) -> None:
        delete_indices(self.__prefix)
        create_indices(self.__prefix)
        upsert_archetypes(self.__prefix)

    def sleep(self, time_: float) -> None:
        time.sleep(time_)


elastic = ElasticFixture(
    get_prefix()
)
