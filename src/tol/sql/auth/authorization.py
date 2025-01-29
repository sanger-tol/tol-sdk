# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from typing import Any, NamedTuple

from sqlalchemy import Column, Integer, String, ForeignKey, BOOLEAN, and_
from sqlalchemy.orm import Mapped, Session, relationship

if typing.TYPE_CHECKING:
    from .models import ModelClass


class NeedABC(ABC):
    @abstractmethod
    @classmethod
    def get_needs(
        cls,
        object_type: str,
        method: str
    ) -> list[NeedABC]:
        pass


class AuthorizationModels(NamedTuple):
    role_mixin: type[Any]
    user_mixin: type[Any]
    membership: ModelClass
    user_membership: ModelClass
    data_object_type: ModelClass
    data_object_type_attribute: ModelClass
    membership_data_object_type: ModelClass
    membership_data_object_type_allowed_attribute: ModelClass
    membership_need: ModelClass
    source: ModelClass
    source_membership: ModelClass
    need: ModelClass
    need_method: ModelClass
    method: ModelClass


def create_authorization_models(
    model_base: ModelClass
) -> AuthorizationModels:

    class RoleMixin:
        id = Column(Integer, primary_key=True)
        name = Column(String)
        system_access = Column(BOOLEAN, default=False)
        '''
            Identifies the role as a elevated role for the access of system attributes
        '''

        user_memberships = relationship("UserMembership", back_populates="role")
        need_methods = relationship("NeedMethod", back_populates="role")

    class AuthzUserMixin:
        id = Column(Integer, primary_key=True)
        username = Column(String)

        user_memberships = relationship("UserMembership", back_populates="user")
        memberships: Mapped[list[Membership]] = relationship('user_membership')

    class Membership(model_base):
        __tablename__ = 'membership'
        id = Column(Integer, primary_key=True)
        parent_id = Column(Integer, ForeignKey('membership.id'))
        name = Column(String)

        parent = relationship("Membership", remote_side=[id], back_populates="children")
        children = relationship("Membership", back_populates="parent")
        user_memberships = relationship("UserMembership", back_populates="membership")
        membership_data_object_types = relationship("MembershipDataObjectType", back_populates="membership")
        data_object_types = relationship("DataObjectType", secondary='membership_data_object_type')
        membership_needs = relationship("MembershipNeed", back_populates="membership")
        source_memberships = relationship("SourceMembership", back_populates="membership")
        membership_data_object_type_allowed_attributes = relationship(
            "MembershipDataObjectTypeAllowedAttribute",
            secondary='membership_data_object_type'
        )

    class UserMembership(model_base):
        __tablename__ = 'user_membership'
        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('user.id'))
        membership_id = Column(Integer, ForeignKey('membership.id'))
        role_id = Column(Integer, ForeignKey('role.id'))

        user = relationship("User", back_populates="user_memberships")
        membership = relationship("Membership", back_populates="user_memberships")
        role = relationship("Role", back_populates="user_memberships")

    class DataObjectType(model_base):
        __tablename__ = 'data_object_type'
        id = Column(Integer, primary_key=True)
        source_id = Column(Integer, ForeignKey('source.id'))
        name = Column(String)

        source = relationship("Source", back_populates="data_object_types")
        membership_data_object_types = relationship("MembershipDataObjectType", back_populates="data_object_type")
        data_object_type_attributes = relationship("DataObjectTypeAttribute", back_populates="data_object_type")
        needs = relationship("Need", back_populates="data_object_type")

    class DataObjectTypeAttribute(model_base):
        __tablename__ = 'data_object_type_attribute'
        id = Column(Integer, primary_key=True)
        data_object_type_id = Column(Integer, ForeignKey('data_object_type.id'))
        name = Column(String)
        system = Column(BOOLEAN, default=False)
        '''
            The system attribute identifies trusted system attributes that requires elevated access to update.
            e.g.: 
                membership_id
                project_id
        '''

        data_object_type = relationship("DataObjectType", back_populates="data_object_type_attributes")
        membership_data_object_type_allowed_attributes = relationship("MembershipDataObjectTypeAllowedAttribute", back_populates="data_object_type_attribute")

    class MembershipDataObjectType(model_base):
        __tablename__ = 'membership_data_object_type'
        id = Column(Integer, primary_key=True)
        membership_id = Column(Integer, ForeignKey('membership.id'))
        data_object_type_id = Column(Integer, ForeignKey('data_object_type.id'))

        membership = relationship("Membership", back_populates="membership_data_object_types")
        data_object_type = relationship("DataObjectType", back_populates="membership_data_object_types")
        membership_data_object_type_allowed_attributes = relationship("MembershipDataObjectTypeAllowedAttribute", back_populates="membership_data_object_type")

    class MembershipDataObjectTypeAllowedAttribute(model_base):
        __tablename__ = 'membership_data_object_type_allowed_attribute'
        id = Column(Integer, primary_key=True)
        membership_data_object_type_id = Column(Integer, ForeignKey('membership_data_object_type.id'))
        data_object_type_attribute_id = Column(Integer, ForeignKey('data_object_type_attribute.id'))

        membership_data_object_type = relationship("MembershipDataObjectType", back_populates="membership_data_object_type_allowed_attributes")
        data_object_type_attribute = relationship("DataObjectTypeAttribute", back_populates="membership_data_object_type_allowed_attributes")

    class MembershipNeed(model_base):
        __tablename__ = 'membership_need'
        id = Column(Integer, primary_key=True)
        membership_id = Column(Integer, ForeignKey('membership.id'))
        need_id = Column(Integer, ForeignKey('need.id'))

        membership = relationship("Membership", back_populates="membership_needs")
        need = relationship("Need", back_populates="membership_needs")

    class Source(model_base):
        __tablename__ = 'source'
        id = Column(Integer, primary_key=True)
        name = Column(String)

        data_object_types = relationship("DataObjectType", back_populates="source")
        source_memberships = relationship("SourceMembership", back_populates="source")

    class SourceMembership(model_base):
        __tablename__ = 'source_membership'
        id = Column(Integer, primary_key=True)
        source_id = Column(Integer, ForeignKey('source.id'))
        membership_id = Column(Integer, ForeignKey('membership.id'))
        source_member_ship_object_name = Column(String)

        source = relationship("Source", back_populates="source_memberships")
        membership = relationship("Membership", back_populates="source_memberships")

    class Need(NeedABC, model_base):
        __tablename__ = 'need'
        id = Column(Integer, primary_key=True)
        data_object_type_id = Column(Integer, ForeignKey('data_object_type.id'))

        data_object_type = relationship("DataObjectType", back_populates="needs")
        membership_needs = relationship("MembershipNeed", back_populates="need")
        need_methods = relationship("NeedMethod", back_populates="need")
        methods: Mapped[list[Method]] = relationship(secondary='need_method')

        def get_needs(
            cls,
            object_type: str,
            method: str,
            session: Session
        ) -> list[tuple[Need, str]]:

            return session.query(
                cls
            ).join(
                DataObjectType,
                DataObjectType.id == cls.data_object_type_id
            ).join(
                NeedMethod,
                NeedMethod.need_id == cls.id
            ).join(
                Method,
                Method.id == NeedMethod.method_id
            ).filter(
                and_(
                    Method.identifier == method,
                    DataObjectType.name == object_type
                )
            ).all()

    class NeedMethod(model_base):
        __tablename__ = 'need_method'
        id = Column(Integer, primary_key=True)
        need_id = Column(Integer, ForeignKey('need.id'))
        method_id = Column(Integer, ForeignKey('method.id'))
        role_id = Column(Integer, ForeignKey('role.id'), nullable=True)

        need = relationship("Need", back_populates="need_methods")
        method = relationship("Method", back_populates="need_methods")
        role = relationship("Role", back_populates="need_methods")

    class Method(model_base):
        __tablename__ = 'method'
        id = Column(Integer, primary_key=True)
        identifier = Column(String)

        need_methods = relationship("NeedMethod", back_populates="method")

    return AuthorizationModels(
        role_mixin=RoleMixin,
        user_mixin=AuthzUserMixin,
        membership=Membership,
        user_membership=UserMembership,
        data_object_type=DataObjectType,
        data_object_type_attribute=DataObjectTypeAttribute,
        membership_data_object_type=MembershipDataObjectType,
        membership_data_object_type_allowed_attribute=MembershipDataObjectTypeAllowedAttribute,
        membership_need=MembershipNeed,
        source=Source,
        source_membership=SourceMembership,
        need=Need,
        need_method=NeedMethod,
        method=Method
    )
