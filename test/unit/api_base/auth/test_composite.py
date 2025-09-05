# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT
from inspect import BoundArguments
from typing import Optional
from unittest.mock import create_autospec, Mock, MagicMock

import pytest

from tol.api_base.auth import (
    CompositeAuthInspector,
    ForbiddenError
)
from tol.api_base.misc import AuthContext
from tol.core.datasource_filter import AndFilter
from tol.core.operator import OperatorMethod


@pytest.fixture(scope='module')
def admin_role() -> str:
    return 'impeccable'


@pytest.fixture(scope='function')
def _auth_ctx() -> AuthContext:
    return create_autospec(
        AuthContext,
        spec_set=True
    )


@pytest.fixture(scope='function')
def auth_inspector(
    admin_role: str,
        _auth_ctx: AuthContext
) -> CompositeAuthInspector:

    return CompositeAuthInspector(
        admin_role=admin_role,
        ctx_getter=lambda: _auth_ctx
    )


class TestCompositeAuthInspector:

    def test_noauth(
        self,
            _auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector
    ) -> None:
        """
        `CompositeAuthInspector().noauth()`
        in isolation
        """

        _auth_ctx.authenticated = False

        @auth_inspector.noauth
        def __raise_error(
            object_type: str,
            op: OperatorMethod,
            **kwargs
        ) -> Optional[AndFilter]:

            if object_type == 'forbidden':
                raise ForbiddenError()

        @auth_inspector.noauth
        def __return_dict1(
            object_type: str,
            op: OperatorMethod,
            **kwargs
        ) -> Optional[AndFilter]:

            return {
                'user.id': {
                    'eq': {
                        'value': 'yes'
                    }
                }
            }

        @auth_inspector.noauth
        def __return_dict2(
            object_type: str,
            op: OperatorMethod,
            **kwargs
        ) -> Optional[AndFilter]:

            return {
                'no_its_not': {
                    'eq': {
                        'value': 'nooo',
                        'negate': True
                    }
                }
            }

        bound_args = Mock(spec=BoundArguments)
        bound_args.arguments = {
            'object_type': 'forbidden',
            'op': OperatorMethod.DETAIL,
            'auth_context': _auth_ctx
        }
        bound_args.kwargs = {'additional_param': 'value'}

        with pytest.raises(ForbiddenError):
            auth_inspector(
                'forbidden',
                OperatorMethod.DETAIL,
                bound_args
            )

        expected = {
            'user.id': {
                'eq': {
                    'value': 'yes'
                }
            },
            'no_its_not': {
                'eq': {
                    'value': 'nooo',
                    'negate': True
                }
            }
        }

        bound_args = Mock(spec=BoundArguments)
        bound_args.arguments = {
            'object_type': 'permitted',
            'op': OperatorMethod.DELETE,
            'auth_context': _auth_ctx
        }
        bound_args.kwargs = {'additional_param': 'value'}

        observed = auth_inspector(
            'permitted',
            OperatorMethod.DELETE,
            bound_args
        )
        assert observed == expected

    def test_admin(
        self,
        admin_role: str,
            _auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector
    ) -> None:
        """
        Users with the admin role can do anything,
        no hooks are called
        """

        _auth_ctx.authenticated = True
        _auth_ctx.roles = [admin_role, 'me_also']

        @auth_inspector.auth
        def __error_if_called(*args):
            raise ForbiddenError()

        bound_args = Mock(spec=BoundArguments)
        bound_args.arguments = {
            'object_type': 'does_not_matter',
            'op': OperatorMethod.UPSERT,
            'auth_context': _auth_ctx
        }
        bound_args.kwargs = {'additional_param': 'value'}

        ext_and = auth_inspector(
            'does_not_matter',
            OperatorMethod.UPSERT,
            bound_args
        )

        assert not ext_and

    def test_auth(
        self,
        _auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector
    ) -> None:
        """
        `CompositeAuthInspector().auth()`
        in isolation
        """

        _auth_ctx.authenticated = True
        _auth_ctx.roles = ['hi']

        @auth_inspector.auth
        def __none(*args, **kwargs):
            return None

        @auth_inspector.auth
        def __empty(*args, **kwargs):
            return {}

        @auth_inspector.auth
        def __dict_if_nice(
            object_type: str,
            op: OperatorMethod,
            auth_ctx: Optional[AuthContext] = None,
            bound_args: Optional[BoundArguments] = None,
        ):

            assert auth_ctx.roles == ['hi']

            if object_type != 'nice':
                return None
            else:
                return {
                    'nicely_done': {
                        'exists': {}
                    }
                }

        _bound_args = Mock(spec=BoundArguments)
        _bound_args.arguments = {
            'object_type': 'nasty',
            'op': OperatorMethod.COUNT,
            'auth_context': _auth_ctx
        }
        _bound_args.kwargs = {'additional_param': 'value'}

        observed_empty = auth_inspector(
            'nasty',
            OperatorMethod.COUNT,
            _bound_args
        )
        assert not observed_empty

        expected = {
            'nicely_done': {
                'exists': {}
            }
        }

        _bound_args = Mock(spec=BoundArguments)
        _bound_args.arguments = {
            'object_type': 'nice',
            'op': OperatorMethod.EXPORT,
            'auth_context': _auth_ctx
        }
        _bound_args.kwargs = {'additional_param': 'value'}

        observed = auth_inspector(
            'nice',
            OperatorMethod.EXPORT,
            _bound_args
        )
        assert observed == expected

    def test_forbid_noauth(
        self,
            _auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector,
        admin_role: str
    ):
        """
        `CompositeAuthInspector().forbid_noauth` only
        impedes unauthenticated requests
        """

        auth_inspector.forbid_noauth('verboten')

        # no authentication
        _auth_ctx.authenticated = False

        bound_args = Mock(spec=BoundArguments)
        bound_args.arguments = {
            'object_type': 'verboten',
            'op': OperatorMethod.COUNT,
            'auth_context': _auth_ctx
        }
        bound_args.kwargs = {'additional_param': 'value'}

        with pytest.raises(ForbiddenError):
            auth_inspector('verboten', OperatorMethod.COUNT, bound_args)

        # no roles user
        _auth_ctx.authenticated = True
        _auth_ctx.roles = []

        bound_args = Mock(spec=BoundArguments)
        bound_args.arguments = {
            'object_type': 'verboten',
            'op': OperatorMethod.TO_MANY,
            'auth_context': _auth_ctx
        }
        bound_args.kwargs = {'additional_param': 'value'}

        auth_inspector('verboten', OperatorMethod.TO_MANY, bound_args)

        # admin user
        _auth_ctx.roles = [admin_role]

        bound_args = Mock(spec=BoundArguments)
        bound_args.arguments = {
            'object_type': 'verboten',
            'op': OperatorMethod.DETAIL,
            'auth_context': _auth_ctx
        }
        bound_args.kwargs = {'additional_param': 'value'}

        auth_inspector('verboten', OperatorMethod.DETAIL, bound_args)

    def test_forbid(
        self,
            _auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector,
        admin_role: str
    ):
        """
        `CompositeAuthInspector().forbid` only
        impedes non-admin requests
        """

        auth_inspector.forbid(['a', 'b', 'c'])

        bound_args = Mock(spec=BoundArguments)
        bound_args.arguments = {
            'object_type': 'c',
            'op': OperatorMethod.COUNT,
            'auth_context': _auth_ctx
        }
        bound_args.kwargs = {'additional_param': 'value'}

        # no authentication
        _auth_ctx.authenticated = False
        with pytest.raises(ForbiddenError):
            auth_inspector('c', OperatorMethod.COUNT, bound_args)

        # no roles user
        _auth_ctx.authenticated = True
        _auth_ctx.roles = []

        bound_args = Mock(spec=BoundArguments)
        bound_args.arguments = {
            'object_type': 'b',
            'op': OperatorMethod.TO_MANY,
            'auth_context': _auth_ctx
        }
        bound_args.kwargs = {'additional_param': 'value'}

        with pytest.raises(ForbiddenError):
            auth_inspector('b', OperatorMethod.TO_MANY, bound_args)

        # admin user
        _auth_ctx.roles = [admin_role]

        bound_args = Mock(spec=BoundArguments)
        bound_args.arguments = {
            'object_type': 'a',
            'op': OperatorMethod.DETAIL,
            'auth_context': _auth_ctx
        }
        bound_args.kwargs = {'additional_param': 'value'}

        auth_inspector('a', OperatorMethod.DETAIL, bound_args)

    def test_ensemble(
        self,
            _auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector
    ) -> None:
        """All methods together"""

        auth_inspector.forbid('fail')

        @auth_inspector.noauth(
            object_type=['a', 'b', 'c']
        )
        def __noauth(*args, **kwargs):
            raise ForbiddenError()

        @auth_inspector.auth
        def __fine(*args, **kwargs):
            return {
                'fine': {
                    'in_list': {
                        'value': [
                            'excellent'
                        ]
                    }
                }
            }

        bound_args = Mock(spec=BoundArguments)
        bound_args.arguments = {
            'object_type': 'a',
            'op': OperatorMethod.STATS,
            'auth_context': _auth_ctx
        }
        bound_args.kwargs = {'additional_param': 'value'}

        _auth_ctx.authenticated = False

        with pytest.raises(ForbiddenError):
            auth_inspector(
                'a',
                OperatorMethod.STATS,
                bound_args
            )

        bound_args = Mock(spec=BoundArguments)
        bound_args.arguments = {
            'object_type': 'fail',
            'op': OperatorMethod.UPDATE,
            'auth_context': _auth_ctx
        }
        bound_args.kwargs = {'additional_param': 'value'}

        _auth_ctx.authenticated = True

        with pytest.raises(ForbiddenError):
            auth_inspector(
                'fail',
                OperatorMethod.UPDATE,
                bound_args
            )

        expected = {
            'fine': {
                'in_list': {
                    'value': [
                        'excellent'
                    ]
                }
            }
        }

        bound_args = Mock(spec=BoundArguments)
        bound_args.arguments = {
            'object_type': 'whatever',
            'op': OperatorMethod.TO_ONE,
            'auth_context': _auth_ctx
        }
        bound_args.kwargs = {'additional_param': 'value'}

        observed = auth_inspector(
            'whatever',
            OperatorMethod.TO_ONE,
            bound_args
        )
        assert observed == expected