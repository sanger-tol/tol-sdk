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
)


class ElasticFixture(DataSourceFixture):
    """A `DataSourceFixture` for `ElasticDataSource`"""

    def __init__(self) -> None:
        wait_for_ready()

    @property
    def name(self) -> str:
        return 'elastic'

    def get_ds_instance(self) -> ElasticDataSource:
        elastic_ds = elastic_datasource()
        core_data_object(elastic_ds)
        return elastic_ds

    def after_test(self) -> None:
        delete_indices()

    def before_test(self) -> None:
        delete_indices()
        create_indices()
        upsert_archetypes()

    def sleep(self, time_: float) -> None:
        time.sleep(time_)


elastic = ElasticFixture()
