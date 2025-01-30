# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from itertools import chain
from typing import Any

from sqlalchemy.orm import Session

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
        session_factory: SessionFactory,
        root_name: str = '*'
    ):

        self.__membership_model = membership_model
        self.__session_factiory = session_factory
        self.__root_name = root_name

    def get_dict(self) -> MembershipTreeNode:
        with self.__session_factiory() as session:
            root_membership = self.__get_root(session)

            return self.__get_dict_below_membership(
                root_membership,
                session
            )

    def get_ids_below_id(self, id_: int) -> set[int]:
        with self.__session_factiory() as session:
            membership = self.__get_membership_by_id(
                id_,
                session
            )

            ids_below = self.__get_ids_below_membership(
                membership,
                session
            )
            ids_below.add(id_)

            return ids_below

    def __get_membership_by_id(
        self,
        id_: int,
        session: Session
    ) -> MembershipABC:

        membership: MembershipABC | None = session.query(
            self.__membership_model
        ).filter_by(
            id=id_
        ).one_or_none()

        if membership is None:
            raise KeyError()

        return membership

    def __get_root(
        self,
        session: Session
    ) -> MembershipABC:

        return session.query(
            self.__membership_model
        ).filter_by(
            name=self.__root_name
        ).one_or_none()

    def __get_direct_children(
        self,
        membership: MembershipABC,
        session: Session
    ) -> list[MembershipABC]:

        return session.query(
            self.__membership_model
        ).filter_by(
            parent_id=membership.id
        ).all()

    def __get_dict_below_membership(
        self,
        membership: MembershipABC,
        session: Session
    ) -> MembershipTreeNode:

        child_memberships = self.__get_direct_children(
            membership,
            session
        )

        return {
            'id': membership.id,
            'name': membership.name,
            'children': [
                self.__get_dict_below_membership(
                    child_membership,
                    session
                )
                for child_membership
                in child_memberships
            ]
        }

    def __get_ids_below_membership(
        self,
        membership: MembershipABC,
        session: Session   
    ) -> set[int]:

        child_memberships = self.__get_direct_children(
            membership,
            session
        )

        chained = chain.from_iterable(
            self.__get_ids_below_membership(
                child_membership,
                session
            )
            for child_membership
            in child_memberships
        )

        below_ids = set(chained)
        below_ids.add(membership.id)

        return below_ids
