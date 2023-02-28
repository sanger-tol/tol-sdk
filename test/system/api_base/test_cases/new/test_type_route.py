# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base import ServiceNamespace

from ...test_case import BaseTestCase


class TestTypeRoute(BaseTestCase):
    def test_simple_type_route(self):
        router = ServiceNamespace()

        # the class to add doc on
        @router.route('/test')
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

    def test_compound_type_route(self):
        # the class to add doc on
        class TestClass:
            @classmethod
            @router.type_route('/test', 'GET')
            def test_get(cls):
                pass
        
            @classmethod
            @router.type_route('/test', 'POST')
            def test_post(cls):
                pass
        
            @classmethod
            @router.type_route('/test', 'DELETE')
            def test_delete(cls):
                pass
        
            @classmethod
            @router.type_route('/test/<id>', 'GET')
            def test_detail_get(cls):
                pass

            @classmethod
            @router.type_route('/test/<id>', 'PATCH')
            def test_detail_patch(cls):
                pass
        
        self.assertTrue(
            hasattr(TestClass, '_doc')
        )
        self.assertEqual(
            TestClass._doc,
            {
                '/test': {
                    'GET': 'test_get',
                    'POST': 'test_post',
                    'DELETE': 'test_delete'
                },
                '/test/<id>': {
                    'GET': 'test_detail_get',
                    'PATCH': 'test_detail_patch'
                }
            }
        )
