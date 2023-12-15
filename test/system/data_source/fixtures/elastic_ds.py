# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from uuid import uuid4

from tol.elastic import ElasticDataSource

from .base import DataSourceFixture


class ElasticFixture(DataSourceFixture):
    """A `DataSourceFixture` for `ElasticDataSource`"""

    def __init__(self) -> None:
        self.__index_prefix = self.__create_index_prefix()

    def __create_index_prefix(self) -> str:
        uuid_ = uuid4().hex
        return f'user-data-tol-test-{uuid_}'

    @property
    def name(self) -> str:
        return 'elastic'

    def get_ds_instance(self) -> ElasticDataSource:
        return ElasticDataSource(
            {
                'uri': os.environ['ELASTIC_URI'],
                'user': os.environ['ELASTIC_USER'],
                'password': os.environ['ELASTIC_PASSWORD'],
                'index_prefix': self.__index_prefix,
                'relationship_cfg': {}
            }
        )

    def after_test(self) -> None:
        pass

    def tear_down(self) -> None:
        pass


elastic = ElasticFixture()
