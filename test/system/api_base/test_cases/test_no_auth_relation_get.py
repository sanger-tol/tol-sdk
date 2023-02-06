# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..test_case import BaseTestCase


class TestNoAuthRelation(BaseTestCase):
    """
    Test that no relation list get endpoints are defined that point /auths
    """
    def test_swagger_json(self):
        response = self.client.open(
            '/api/v1/swagger.json',
            method='GET',
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        swagger = response.json
        endpoints_paths = list(swagger['paths'].keys())
        split_endpoints = {
            e: e.split('/') for e in endpoints_paths
        }
        relation_list_get_targets = {
            e: s[-1] for e, s  # pull out the target
            in split_endpoints.items()
            if len(s) > 3  # if it's a relation list get endpoint
        }
        for endpoint, target in relation_list_get_targets.items():
            assert target != 'auth', (
                f'The endpoint {endpoint} maps to the auth resource. '
                'This could lead to token disclosure.'
            )

    def test_no_auth_regression(self):
        """
        This checks that TOLP-5219 hasn't returned
        """
        response = self.client.open(
            '/api/v1/users',
            method='GET',
        )
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
