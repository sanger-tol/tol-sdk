# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ...test_case import BaseTestCase


class TestEnumSwaggerJson(BaseTestCase):
    def _get_swagger_json_file(self):
        response = self.client.open(
            '/api/v1/swagger.json',
            method='GET'
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        return response.json

    def test_all_enum_paths_in_swagger(self):
        swagger_json = self._get_swagger_json_file()
        paths = list(swagger_json['paths'].keys())

        # assert that all I (enum) paths (including name) are in there
        assert '/enum/i' in paths
        assert '/enum/i/{name}' in paths
        assert '/enum/i/{name}/j' in paths

        # assert that other (non-enum) endpoints do not have name paths
        assert '/b/{name}' not in paths
        assert '/b/{name}/e' not in paths
        assert '/enum/b/{name}' not in paths
        assert '/enum/b/{name}/e' not in paths
