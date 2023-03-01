# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base import ServiceNamespace, Swagger, fields

from ...test_case import BaseTestCase


class TestNSWithSwagger(BaseTestCase):
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
        # the class to add doc on
        @ns_test.route('/test')
        class TestService:
            @ns_test.doc(
                responses={
                    '200': (
                        'Success',
                        test_swagger
                    ),
                    '400': 'Bad Request',
                    '404': 'Not Found'
                }
            )
            def get(self):
                pass

        self.assertTrue(
            hasattr(TestService, '_doc')
        )
        self.assertEqual(
            TestService._doc,
            {
                'path': '/test'
            }
        )
