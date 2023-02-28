# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base import ServiceNamespace

from ...test_case import BaseTestCase


class TestRoute(BaseTestCase):
    def test_simple_route(self):
        ns_test = ServiceNamespace()

        # the class to add doc on
        @ns_test.route('/test')
        class TestService:
            @classmethod
            def get(cls):
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
