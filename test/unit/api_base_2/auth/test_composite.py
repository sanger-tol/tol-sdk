# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Optional
from unittest.mock import create_autospec

import pytest

from tol.api_base2.auth import (
    CompositeAuthInspector,
    ForbiddenError
)
from tol.api_base2.misc import AuthContext
from tol.core.datasource_filter import AndFilter
from tol.core.operator import OperatorMethod


@pytest.fixture(scope='module')
def admin_role() -> str:
    return 'impeccable'


@pytest.fixture(scope='function')
def auth_ctx() -> AuthContext:
    return create_autospec(
        AuthContext,
        spec_set=True
    )


@pytest.fixture(scope='function')
def auth_inspector(
    admin_role: str,
    auth_ctx: AuthContext
) -> CompositeAuthInspector:

    return CompositeAuthInspector(
        admin_role=admin_role,
        ctx_getter=lambda: auth_ctx
    )


class TestCompositeAuthInspector:

    def test_noauth(
        self,
        auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector
    ) -> None:
        """
        `CompositeAuthInspector().noauth()`
        in isolation
        """

        auth_ctx.authenticated = False

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

        with pytest.raises(ForbiddenError):
            auth_inspector(
                'forbidden',
                OperatorMethod.DETAIL
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
        observed = auth_inspector(
            'permitted',
            OperatorMethod.DELETE
        )
        assert observed == expected

    def test_admin(
        self,
        admin_role: str,
        auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector
    ) -> None:
        """
        Users with the admin role can do anything,
        no hooks are called
        """

        auth_ctx.authenticated = True
        auth_ctx.roles = [admin_role, 'me_also']

        @auth_inspector.auth
        def __error_if_called(*args):
            raise ForbiddenError()

        ext_and = auth_inspector(
            'does_not_matter',
            OperatorMethod.UPSERT
        )

        assert not ext_and

    def test_auth(
        self,
        auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector
    ) -> None:
        """
        `CompositeAuthInspector().auth()`
        in isolation
        """

        auth_ctx.authenticated = True
        auth_ctx.roles = ['hi']

        @auth_inspector.auth
        def __none(*args, **kwargs):
            return None

        @auth_inspector.auth
        def __empty(*args, **kwargs):
            return {}

        @auth_inspector.auth
        def __dict_if_nice(
            object_type: str,
            *args,
            auth_context: Optional[AuthContext] = None
        ):

            assert auth_context.roles == ['hi']

            if object_type != 'nice':
                return None
            else:
                return {
                    'nicely_done': {
                        'exists': {}
                    }
                }

        observed_empty = auth_inspector(
            'nasty',
            OperatorMethod.COUNT
        )
        assert not observed_empty

        expected = {
            'nicely_done': {
                'exists': {}
            }
        }
        observed = auth_inspector(
            'nice',
            OperatorMethod.EXPORT
        )
        assert observed == expected

    def test_forbid_noauth(
        self,
        auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector,
        admin_role: str
    ):
        """
        `CompositeAuthInspector().forbid_noauth` only
        impedes unauthenticated requests
        """

        auth_inspector.forbid_noauth('verboten')

        # no authentication
        auth_ctx.authenticated = False
        with pytest.raises(ForbiddenError):
            auth_inspector('verboten', OperatorMethod.COUNT)

        # no roles user
        auth_ctx.authenticated = True
        auth_ctx.roles = []
        auth_inspector('verboten', OperatorMethod.TO_MANY)

        # admin user
        auth_ctx.roles = [admin_role]
        auth_inspector('verboten', OperatorMethod.DETAIL)

    def test_forbid(
        self,
        auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector,
        admin_role: str
    ):
        """
        `CompositeAuthInspector().forbid` only
        impedes non-admin requests
        """

        auth_inspector.forbid(['a', 'b', 'c'])

        # no authentication
        auth_ctx.authenticated = False
        with pytest.raises(ForbiddenError):
            auth_inspector('c', OperatorMethod.COUNT)

        # no roles user
        auth_ctx.authenticated = True
        auth_ctx.roles = []
        with pytest.raises(ForbiddenError):
            auth_inspector('b', OperatorMethod.TO_MANY)

        # admin user
        auth_ctx.roles = [admin_role]
        auth_inspector('a', OperatorMethod.DETAIL)

    def test_ensemble(
        self,
        auth_ctx: AuthContext,
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

        auth_ctx.authenticated = False

        with pytest.raises(ForbiddenError):
            auth_inspector(
                'a',
                OperatorMethod.STATS
            )

        auth_ctx.authenticated = True

        with pytest.raises(ForbiddenError):
            auth_inspector(
                'fail',
                OperatorMethod.UPDATE
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
        observed = auth_inspector(
            'whatever',
            OperatorMethod.TO_ONE
        )
        assert observed == expected
