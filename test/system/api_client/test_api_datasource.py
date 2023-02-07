# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_client import (
    ApiDataSource
)


class TestApiDataSource(ApiDataSource):
    def __init__(self, config):
        super(TestApiDataSource, self).__init__(config)
        self.get_count = 0
        self.post_count = 0
        self.patch_count = 0
        self.delete_count = 0

    def _get(self, path, params):
        response = self.client.get(f'/api/v1{path}', query_string=params)
        self.get_count += 1
        return response

    def _post(self, path, json):
        response = self.client.post(f'/api/v1{path}', json=json,
                                    headers={'Token': self.key})
        self.post_count += 1
        return response

    def _patch(self, path, json):
        response = self.client.patch(f'/api/v1{path}', json=json,
                                     headers={'Token': self.key})
        self.patch_count += 1
        return response

    def _delete(self, path):
        response = self.client.delete(f'/api/v1{path}',
                                      headers={'Token': self.key})
        self.delete_count += 1
        return response
