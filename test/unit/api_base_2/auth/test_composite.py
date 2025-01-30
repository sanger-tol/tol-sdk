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
