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

        expected = {
            'id': 1,
            'name': 'Sanger Institute',
            'children': [
                {
                    'id': 2,
                    'name': 'Genomics',
                    'children': [
                        {
                            'id': 4,
                            'name': 'Genomics Research',
                            'children': [
                                {
                                    'id': 7,
                                    'name': 'Bioinformatics',
                                    'children': []
                                },
                                {
                                    'id': 8,
                                    'name': 'Genomic Analysis',
                                    'children': []
                                }
                            ]
                        },
                        {
                            'id': 5,
                            'name': 'Genomics Services',
                            'children': []
                        }
                    ]
                },
                {
                    'name': 'Informatics',
                    'id': 3,
                    'children': [
                        {
                            'name': 'Informatics Research',
                            'id': 6,
                            'children': []
                        }
                    ]
                }
            ]
        }

        observed = tree_manager.get_dict()

        assert observed == expected

    def test_get_ids_below_id__good(
        self,
        tree_manager: MembershipTreeManager
    ):
        pass

    def test_get_ids_below_id__key_error(
        self,
        tree_manager: MembershipTreeManager
    ):
        pass
