# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.api_base import (
    BadHTTPMethodException,
    NoHTTPMethodsException,
    ServiceNamespace
)
from tol.api_base.service.namespace import ServiceConfig, ServiceMethodConfig, ServiceMethodResponse


class TestRoute:
    def test_simple_route(self):
        ns_test = ServiceNamespace()

        # the class to add doc on
        @ns_test.route('/test')
        class TestService:
            def get(self):
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
            def get(self):
                pass

        # the second class to add doc on
        @ns_test.route('/test/second')
        class TestService2:
            def get(self):
                pass

        assert hasattr(TestService1, '_doc')
        assert TestService1._doc == {
            'path': '/test'
        }
        assert hasattr(TestService2, '_doc')
        assert TestService2._doc == {
            'path': '/test/second'
        }

    def test_function_doc_bad_method(self):
        ns_test = ServiceNamespace()

        with pytest.raises(BadHTTPMethodException):
            # the class with a nonsense method
            @ns_test.route('/test')
            class TestService: # noqa
                @ns_test.response(200)
                def nonsense(self):
                    pass

                def patch(self):
                    pass

    def test_multiple_methods_configure_correctly(self):
        ns_test = ServiceNamespace()

        @ns_test.route('/test')
        class TestService:
            def get(self):
                pass

            @ns_test.response(
                200,
                description='Success'
            )
            def post(self):
                pass

            def nonsense(self):
                pass

        @ns_test.route('/test/<id>')
        class TestServiceDetail:
            def get(self, id_: int):
                pass

            @ns_test.response(
                204,
                description='Success'
            )
            def delete(self, id_: int):
                pass

            def nonsense(self, id_: int):
                pass

        http_methods = ns_test.to_dict()
        assert len(http_methods) == 2
        assert set(http_methods.keys()) == {
            '/test',
            '/test/<id>'
        }
        assert http_methods == {
            '/test': ServiceConfig(
                service=TestService,
                methods={
                    'get': ServiceMethodConfig(),
                    'post': ServiceMethodConfig(
                        responses={
                            200: ServiceMethodResponse(
                                description='Success'
                            )
                        }
                    )
                }
            ),
            '/test/<id>': ServiceConfig(
                service=TestServiceDetail,
                methods={
                    'get': ServiceMethodConfig(),
                    'delete': ServiceMethodConfig(
                        responses={
                            204: ServiceMethodResponse(
                                description='Success'
                            )
                        }
                    )
                }
            )
        }

    def test_service_doc_with_no_http_methods(self):
        ns_test = ServiceNamespace()

        with pytest.raises(NoHTTPMethodsException):
            # the class with no http methods
            @ns_test.route('/test')
            class TestService: # noqa
                def nonsense(self):
                    pass
