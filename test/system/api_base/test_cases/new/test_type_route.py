# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base import ServiceNamespace

from ...test_case import BaseTestCase


class TestTypeRoute(BaseTestCase):
    def test_simple_type_route(self):
        api_test = ServiceNamespace()

        # the class to add doc on
        @api_test.route('/test')
        class TestClass:
            @classmethod
            def get(cls):
                pass

        self.assertTrue(
            hasattr(TestClass, '_doc')
        )
        self.assertEqual(
            TestClass._doc,
            {
                'path': '/test'
            }
        )
