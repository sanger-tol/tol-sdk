# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.api_base import deferred_attr

# TODO:
# - func._declared_attr is set to True
#   only if decorated
# - calling the function sets the attribute
# - the actual function is not called upon
#   decoration


class TestDeclaredAttr:
    def test_declared_attr_set_when_decorated(self):
        class TestExampleClass:
            # regular attribute
            fun = True

            # declared attribute
            @deferred_attr
            def also_fun(self):
                return 'yes'

        assert hasattr(TestExampleClass, 'also_fun')
        assert hasattr(TestExampleClass.also_fun, '_deferred_attr')
        assert TestExampleClass.also_fun._deferred_attr is True

    def test_declared_attr_unset_when_not_decorated(self):
        class TestExampleClass:
            # regular attribute
            fun = True

            def also_fun(self):
                return 'yes'

        assert hasattr(TestExampleClass, 'also_fun')
        assert not hasattr(TestExampleClass.also_fun, '_deferred_attr')
