# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base import ServiceNamespace, Swagger, fields


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
            @ns_test.doc(
                responses=responses
            )
            def get(self):
                pass

        assert hasattr(TestService.get, '_doc')
        assert TestService.get._doc == {
            'responses': responses
        }
