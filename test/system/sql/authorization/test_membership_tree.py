# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any

import pytest

from tol.sql.auth import DbAuthBlueprint
from tol.sql.auth.authorization import MembershipABC
from tol.sql.auth.membership_tree import MembershipTreeManager
from tol.sql.session import SessionFactory


@pytest.fixture
def membership_model(
    auth_bp: DbAuthBlueprint
) -> MembershipABC:

    return auth_bp.models.membership


@pytest.fixture
def tree_manager(
    membership_model: MembershipABC,
    session_factory: SessionFactory
) -> MembershipTreeManager:

    return MembershipTreeManager(
        membership_model,
        session_factory
    )


class TestTreeManager:
    """
    Read operations on the hierachy tree of `Membership`.
    """

    def test_get_dict(
        self,
        tree_manager: MembershipTreeManager
    ):
        pass

    def test_get_dict_below_name__good(
        self,
        tree_manager: MembershipTreeManager
    ):
        pass

    def test_get_dict_below_name__key_error(
        self,
        tree_manager: MembershipTreeManager
    ):
        pass

    def test_get_ids_below_name__good(
        self,
        tree_manager: MembershipTreeManager
    ):
        pass

    def test_get_ids_below_name__key_error(
        self,
        tree_manager: MembershipTreeManager
    ):
        pass
