# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base import type_route

from ...test_case import BaseTestCase


class TestTypeRoute(BaseTestCase):
    def test_simple_type_route(self):
        # the class to add doc on
        class TestClass:
            @classmethod
            @type_route('/test', 'GET')
            def test_method(cls):
                pass
        
        self.assertTrue(
            hasattr(TestClass, '_doc')
        )
        self.assertEqual(
            TestClass._doc,
            {
                '/test': {
                    'GET': TestClass.test_method
                }
            }
        )
