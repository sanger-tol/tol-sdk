# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base import BadHTTPMethodException, ServiceNamespace


class TestRoute:
    def test_simple_route(self):
        ns_test = ServiceNamespace()

        # the class to add doc on
        @ns_test.route('/test')
        class TestService:
            pass

        assert hasattr(TestService, '_doc')
        assert TestService._doc == {
            'path': '/test'
        }

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

        assert hasattr(TestService1, '_doc')
        assert TestService1._doc == {
            'path': '/test'
        }
        assert hasattr(TestService2, '_doc')
        assert TestService2._doc == {
            'path': '/test/second'
        }

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

        assert hasattr(TestService.get, '_doc')
        assert TestService.get._doc == doc

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

    def test_multiple_methods_configure_correctly(self):
        ns_test = ServiceNamespace()

        @ns_test.route('/test')
        class TestService:
            def get(self):
                pass

            @ns_test.doc(
                responses={
                    200: 'Success'
                }
            )
            def post(self):
                pass

            def nonsense(self):
                pass

        @ns_test.route('/test/<id>')
        class TestServiceDetail:
            def get(self, id_: int):
                pass

            @ns_test.doc(
                responses={
                    204: 'Success'
                }
            )
            def delete(self, id_: int):
                pass

            def nonsense(self, id_: int):
                pass

        http_methods = ns_test.identify_http_methods()
        assert len(http_methods) == 2
        assert set(http_methods.keys()) == {
            '/test',
            '/test/<id>'
        }
        assert http_methods == {
            '/test': {
                'get': TestService.get,
                'post': TestService.post
            },
            '/test/<id>': {
                'get': TestServiceDetail.get,
                'delete': TestServiceDetail.delete
            }
        }
