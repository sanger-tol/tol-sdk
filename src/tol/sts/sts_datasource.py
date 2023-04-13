# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import (Dict)

import requests

from ..api_client import (
    ApiDataSource
)
from ..core import (
    unsupported
)


class StsDataSource(ApiDataSource):
    """
    This class extends ApiDataSource to expose native STS endpoints.
    From the ApiDataSource point of view this is read-only, however
    native endpoints are read-write.
    """
    def __init__(self, config: Dict):
        """Initialises an STS data source.

        We expect the following keys in the config:
        url -- the URL of the instance (including path with API prefix)
        key -- the API key to use for authentication
        """
        super().__init__(config)
        self.native_url = self.url
        self.url = f'{self.native_url}/api-base'  # This is where all the API Base endpoints are

    def __override_method(self, method, relative_url, headers=None, **kwargs):
        if headers is None:
            new_headers = {
                'Authorization': self.key
            }
        else:
            new_headers = {
                'Authorization': self.key,
                **headers
            }
        return method(
            f'{self.native_url}/{relative_url}',
            headers=new_headers,
            **kwargs
        )

    def native_get(self, relative_url, **kwargs):
        return self.__override_method(
            requests.get,
            relative_url,
            **kwargs
        )

    def native_post(self, relative_url, **kwargs):
        return self.__override_method(
            requests.post,
            relative_url,
            **kwargs
        )

    def native_put(self, relative_url, **kwargs):
        return self.__override_method(
            requests.put,
            relative_url,
            **kwargs
        )

    def native_patch(self, relative_url, **kwargs):
        return self.__override_method(
            requests.patch,
            relative_url,
            **kwargs
        )

    def native_delete(self, relative_url, **kwargs):
        return self.__override_method(
            requests.delete,
            relative_url,
            **kwargs
        )

    @unsupported('StsDataSource is readonly when used as an ApiDataSource')
    def upsert(self, object_type: str, *args, **kwargs) -> None:
        pass
