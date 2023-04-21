# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Dict, Iterable, List

import requests

from .api_object_serializer import ApiDataSerializer
from ..core import (
    DataObject,
    DataSource,
    DataSourceSession,
    unsupported
)


class ApiDataSource(DataSource):

    def __init__(self, config: Dict):
        """Initialises an API base data source.

        We expect the following keys in the config:
        url -- the URL of the instance (including path with API prefix)
        key -- the API key to use for authentication
        """
        super().__init__(config, expected=['url', 'key'])

    def session(self) -> DataSourceSession:
        """
        Returns a DataSourceSession object for batching upserts.

        On ApiDataSource, this always sends multiple types at the
        same time.
        """
        return DataSourceSession(self, multi_type=True)

    @unsupported()
    def get_by_id(self, object_type: str, *args, **kwargs):
        pass

    @unsupported()
    def get_list(self, object_type: str, *args, **kwargs):
        pass

    @unsupported()
    def get_list_page(self, object_type: str, *args, **kwargs):
        pass

    @unsupported()
    def upsert(self, object_type: str, *args, **kwargs) -> None:
        pass

    def upsert_multiple_type(
        self,
        data_objects: Iterable[DataObject],
        **kwargs
    ) -> None:
        upsert_data = ApiDataSerializer().dump(data_objects)
        if len(upsert_data) == 0:
            return
        self.__perform_upsert(upsert_data)

    def __perform_upsert(self, upsert_data: List[Dict[str, Any]]) -> None:
        r = requests.post(
            f'{self.url}/upsert',
            json=upsert_data,
            headers={'Token': self.key}
        )
        r.raise_for_status()
