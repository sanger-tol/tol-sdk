# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import time

from tol.core import core_data_object
from tol.elastic import ElasticDataSource

from .base import DataSourceFixture
from ..services.util import (
    create_indices,
    delete_aliases,
    elastic_datasource,
    get_prefix,
    upsert_archetypes,
    wait_for_delete,
    wait_for_ready,
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
        delete_aliases(self.__prefix)

    def before_test(self) -> None:
        delete_aliases(self.__prefix, ignore=[404])
        wait_for_delete(
            self.get_ds_instance().es,
            self.__prefix,
        )
        create_indices(self.__prefix)
        upsert_archetypes(self.__prefix)

    def sleep(self, time_: float) -> None:
        time.sleep(time_)


elastic = ElasticFixture(
    get_prefix()
)
