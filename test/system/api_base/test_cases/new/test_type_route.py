# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base import BadHTTPMethodException, ServiceNamespace

from ...test_case import BaseTestCase


class TestRoute(BaseTestCase):
    def test_simple_route(self):
        ns_test = ServiceNamespace()

        # the class to add doc on
        @ns_test.route('/test')
        class TestService:
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
        self.assertEqual(
            len(ns_test.services),
            1
        )
        self.assertEqual(
            ns_test.services[0],
            TestService
        )

    def test_complex_route(self):
        ns_test = ServiceNamespace()

        # the first class to add doc on
        @ns_test.route('/test')
        class TestService1:
            pass

        # the second class to add doc on
        @ns_test.route('/test/second')
        class TestService2:
            pass

        self.assertTrue(
            hasattr(TestService1, '_doc')
        )
        self.assertEqual(
            TestService1._doc,
            {
                'path': '/test'
            }
        )
        self.assertTrue(
            hasattr(TestService2, '_doc')
        )
        self.assertEqual(
            TestService2._doc,
            {
                'path': '/test/second'
            }
        )

        self.assertEqual(
            len(ns_test.services),
            2
        )
        self.assertEqual(
            ns_test.services,
            [TestService1, TestService2]
        )

    def test_function_doc(self):
        ns_test = ServiceNamespace()

        doc = {
            'params': {
                'page': {
                    'in': 'query',
                    'type': 'integer',
                    'description': 'The page of the results.' # noqa
                },
            },
            'responses': {
                200: 'Success'
            }
        }

        # the class to add doc on
        @ns_test.route('/test')
        class TestService:
            @ns_test.doc(**doc)
            def get(self):
                pass

        self.assertTrue(
            hasattr(TestService.get, '_doc')
        )
        self.assertEqual(
            TestService.get._doc,
            doc
        )

    def test_function_doc_bad_method(self):
        ns_test = ServiceNamespace()

        doc = {
            'params': {
                'page': {
                    'in': 'query',
                    'type': 'integer',
                    'description': 'The page of the results.' # noqa
                },
            },
            'responses': {
                200: 'Success'
            }
        }
        with pytest.raises(BadHTTPMethodException):
            # the class with a nonsense method
            @ns_test.route('/test')
            class TestService: # noqa
                @ns_test.doc(**doc)
                def nonsense(self):
                    pass
