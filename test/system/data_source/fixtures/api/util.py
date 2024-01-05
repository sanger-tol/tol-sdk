# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_client2 import ApiDataSource, create_api_datasource
from tol.core.factory import core_data_object

from ..base import DataSourceFixture


TOKEN = 'hypeTrain123!'


class ApiFixture(DataSourceFixture):

    def __init__(
        self,
        backing_fixture: DataSourceFixture,
        host: str,
        port: int = 5000
    ) -> None:

        self.__url = f'http://{host}:{port}'
        self.__backer = backing_fixture
        self.__name = f'api -> {self.__backer.name}'

    @property
    def name(self) -> str:
        return self.__name

    def get_ds_instance(self) -> ApiDataSource:
        api_ds = create_api_datasource(self.__url, token=TOKEN)
        core_data_object(api_ds)
        return api_ds

    def after_test(self) -> None:
        self.__backer.after_test()
