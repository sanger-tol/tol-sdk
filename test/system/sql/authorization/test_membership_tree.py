# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

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

        expected_mapping: dict[int, set[int]] = {
            1: set(range(1, 9)),  # root -> all ID's 1-8
            2: {2, 4, 5, 7, 8},
            4: {4, 7, 8},  # always contains given ID
            6: {},  # leaf node only returns its own ID
        }

        for in_, expected in expected_mapping.items():
            observed = tree_manager.get_ids_below_id(in_)

            assert observed == expected

    def test_get_ids_below_id__key_error(
        self,
        tree_manager: MembershipTreeManager
    ):

        with pytest.raises(KeyError):
            # obviously out of range
            tree_manager.get_ids_below_id(100)
