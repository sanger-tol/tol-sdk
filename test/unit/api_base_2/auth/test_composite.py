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

    def test_handle_noauth(
        self,
        auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector
    ) -> None:
        """
        `CompositeAuthInspector().handle_noauth()`
        in isolation
        """

        auth_ctx.authenticated = False

        @auth_inspector.handle_noauth
        def __raise_error(
            object_type: str,
            op: OperatorMethod,
            **kwargs
        ) -> Optional[AndFilter]:

            if object_type == 'forbidden':
                raise ForbiddenError()

        @auth_inspector.handle_noauth
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

        @auth_inspector.handle_noauth
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

    def test_handle_admin(
        self,
        admin_role: str,
        auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector
    ) -> None:
        """
        Users with the admin role can do anything,
        no handlers are called
        """

        auth_ctx.authenticated = True
        auth_ctx.roles = [admin_role, 'me_also']

        @auth_inspector.handle
        def __error_if_called(*args):
            raise ForbiddenError()

        ext_and = auth_inspector(
            'does_not_matter',
            OperatorMethod.UPSERT
        )

        assert not ext_and

    def test_handle(
        self,
        auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector
    ) -> None:
        """
        `CompositeAuthInspector().handle()`
        in isolation
        """

        auth_ctx.authenticated = True
        auth_ctx.roles = ['hi']

        @auth_inspector.handle
        def __none(*args, **kwargs):
            return None

        @auth_inspector.handle
        def __empty(*args, **kwargs):
            return {}

        @auth_inspector.handle
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

    def test_ensemble(
        self,
        auth_ctx: AuthContext,
        auth_inspector: CompositeAuthInspector
    ) -> None:
        """All methods together"""

        @auth_inspector.handle_type('fail')
        def __fail(*args, **kwargs):
            raise ForbiddenError()

        @auth_inspector.handle_noauth
        def __noauth(*args, **kwargs):
            raise ForbiddenError()

        @auth_inspector.handle
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
                'does not matter',
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
