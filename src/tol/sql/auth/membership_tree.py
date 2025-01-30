# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any

from .authorization import MembershipABC
from ..session import SessionFactory


MembershipTreeNode = dict[
    str,
    (
        int | # id
        str | # name
        list['MembershipTreeNode']  # children
    )
]


class MembershipTreeManager:
    """
    Supports querying the membership tree and
    (selectively) rendering it as JSON
    """

    def __init__(
        self,
        membership_model: MembershipABC,
        session_factory: SessionFactory
    ):

        self.__membership_model = membership_model
        self.__session_factiory = session_factory

    def get_dict(self) -> MembershipTreeNode:
        pass

    def get_ids_below_id(self, id_: int) -> list[int]:
        pass
