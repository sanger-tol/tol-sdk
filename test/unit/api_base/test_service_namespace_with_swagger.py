# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from re import S
from tol.api_base import ServiceNamespace, Swagger, fields
from tol.api_base.service.namespace import ServiceMethodResponse


class TestNSWithSwagger:
    def test_doc_with_swagger(self):
        ns_test = ServiceNamespace()

        # create the swagger
        test_swagger = Swagger(
            'Test',
            {
                'test_value': fields.String(),
                'test_bool': fields.Boolean()
            }
        )

        responses = {
            '200': (
                'Success',
                test_swagger
            ),
            '400': 'Bad Request',
            '404': 'Not Found'
        }

        # the class to add doc on
        @ns_test.route('/test')
        class TestService:
            @ns_test.response(
                200,
                description='get',
                swagger=test_swagger
            )
            @ns_test.response(
                400,
                description='Bad Request'
            )
            @ns_test.response(
                404,
                description='Not Found'
            )
            @ns_test.expects(
                test_swagger
            )
            def get(self):
                pass

        assert hasattr(TestService.get, '_doc')
        assert TestService.get._doc == {
            'responses': {
                404: ServiceMethodResponse(
                    description='Not Found'
                ),
                400: ServiceMethodResponse(
                    description='Bad Request'
                ),
                200: ServiceMethodResponse(
                    description='get',
                    swagger=test_swagger
                )
            },
            'expects': test_swagger
        }
