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

    def test_compound_type_route(self):
        # the class to add doc on
        class TestClass:
            @classmethod
            @type_route('/test', 'GET')
            def test_get(cls):
                pass
        
            @classmethod
            @type_route('/test', 'POST')
            def test_post(cls):
                pass
        
            @classmethod
            @type_route('/test', 'DELETE')
            def test_delete(cls):
                pass
        
            @classmethod
            @type_route('/test/<id>', 'GET')
            def test_detail_get(cls):
                pass

            @classmethod
            @type_route('/test/<id>', 'PATCH')
            def test_detail_patch(cls):
                pass
        
        self.assertTrue(
            hasattr(TestClass, '_doc')
        )
        self.assertEqual(
            TestClass._doc,
            {
                '/test': {
                    'GET': TestClass.test_get,
                    'POST': TestClass.test_post,
                    'DELETE': TestClass.test_delete
                },
                '/test/<id>': {
                    'GET': TestClass.test_detail_get,
                    'PATCH': TestClass.test_detail_patch
                }
            }
        )
