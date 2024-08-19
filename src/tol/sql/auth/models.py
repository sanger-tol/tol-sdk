# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, NamedTuple, Optional
from uuid import uuid4

from sqlalchemy import (
    ForeignKey,
    String,
    delete,
    select
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import (
    Mapped,
    Session,
    mapped_column,
    relationship
)


ModelClass = type[Any]


class AuthUser(ABC):
    """
    Adds authentication ability to a separate `User` class.
    """

    id: int  # noqa A003

    _tokens: list[AuthToken]
    _roles: list[AuthRole]

    @classmethod
    @abstractmethod
    def get_or_create(
        cls,
        sess: Session,
        oidc_id: str,
        **oidc_ext
    ) -> AuthUser:
        """
        Adds a new `User` row to the DB, with the
        given `oidc_id`, if it doesn't already exist.

        Returns the found row if it does.
        """

    @property
    @abstractmethod
    def role_names(self) -> list[str]:
        """
        A `list[str]` of roles assigned to this user.
        """


class AuthState(ABC):
    """
    Stores state between requests within the same
    OIDC handshake.
    """

    @classmethod
    @abstractmethod
    def add(cls, sess: Session) -> str:
        """
        Adds a `State` row to the DB, with a generated
        UUID. Returns the UUID `str`.
        """

    @classmethod
    @abstractmethod
    def exists(cls, sess: Session, uuid: str) -> str:
        """
        Returns `True` if a state with the given `uuid`
        exists.
        """

    @classmethod
    @abstractmethod
    def delete_old(cls, sess: Session, before: datetime) -> None:
        """
        Deletes all `State` rows older than the given
        `before`.
        """


class AuthToken(ABC):
    """Stores a token against a user."""

    user_id: str
    user: Optional[AuthUser]

    @classmethod
    @abstractmethod
    def get(
        cls,
        sess: Session,
        token: str
    ) -> Optional[AuthToken]:
        """
        Gets the `Token` instance with given value. Returns
        `None` if none is found.
        """

    @classmethod
    @abstractmethod
    def get_or_create(
        cls,
        sess: Session,
        token: str,
        user_id: int
    ) -> dict[str, str]:
        """
        Registers the token value against the `User` row
        of given `user_id`. Returns extra details about the
        token, as a `dict[str, str]`.
        """

    @classmethod
    @abstractmethod
    def delete(cls, sess: Session, token: str) -> None:
        """Deletes the row for the given `token`."""

    @classmethod
    @abstractmethod
    def delete_expired(cls, sess: Session) -> None:
        """Deletes expired tokens."""


class AuthRole:
    """A role, any number of which can be assigned to a user."""

    name: str


class AuthRoleBinding:
    """An assignment of a role to a user."""

    user_id: str
    role_id: str


class ModelTuple(NamedTuple):
    """
    Contains the `ModelClass` variables required
    for OIDC in a database.
    """

    state_class: type[AuthState]
    user_class: type[AuthUser]
    token_class: type[AuthToken]
    role_class: type[AuthRole]
    role_binding_class: type[AuthRoleBinding]


def create_models(
    model_base: ModelClass,
    user_table_name: str,
    oidc_id_column_name: str,
    user_mixin_class: ModelClass,
    token_mixin_class: ModelClass,
    token_is_pk: bool,
    role_mixin_class: ModelClass,
    token_expiry_delta: timedelta,
    prefix_with_name: bool
) -> ModelTuple:
    """
    Creates the OIDC db models, given a suitable base (and
    the name of the `User` model.)

    Returns a `NamedTuple`.
    """

    class State(AuthState, model_base):

        __tablename__ = 'oidc_state'

        id: Mapped[str] = mapped_column(  # noqa A003
            primary_key=True,
            name=None if not prefix_with_name else 'state_id'
        )

        created_at: Mapped[datetime] = mapped_column(
            nullable=False,
            default=lambda: datetime.now()
        )

        @classmethod
        def add(cls, sess: Session) -> str:
            state_uuid = uuid4().hex

            sess.add(
                cls(id=state_uuid)
            )
            sess.commit()

            return state_uuid

        @classmethod
        def exists(
            cls,
            sess: Session,
            uuid: str
        ) -> str:

            stmt = select(cls).where(
                cls.id == uuid
            )
            rows = sess.execute(stmt)

            return len(list(rows)) > 0

        @classmethod
        def delete_old(
            cls,
            sess: Session,
            before: datetime
        ) -> None:

            stmt = delete(cls).where(
                cls.created_at < before
            )
            sess.execute(stmt)
            sess.commit()

    oidc_id_column: Mapped[str] = mapped_column(
        type_=String(),
        unique=True,
        nullable=False
    )

    oidc_id_mixin_class = type(
        'OidcIdMixin',
        (object,),
        {
            oidc_id_column_name: oidc_id_column,
            '__abstract__': True
        }
    )

    class User(
        AuthUser,
        model_base,
        oidc_id_mixin_class,
        user_mixin_class,
    ):

        __tablename__ = user_table_name

        id: Mapped[int] = mapped_column(  # noqa A003
            primary_key=True,
            autoincrement=True,
            name=None if not prefix_with_name else 'user_id'
        )

        _tokens: Mapped[list['Token']] = relationship(
            back_populates='user'
        )
        _role_bindings: Mapped[list['RoleBinding']] = relationship(
            back_populates='user'
        )

        @classmethod
        def __get_oidc_id_column_name(cls) -> str:
            """
            Reliably gets the ID column of this `User` against
            the OIDC provider - irrespective of its name.
            """
            return getattr(cls, oidc_id_column_name).name

        @classmethod
        def __one_or_none(
            cls,
            sess: Session,
            oidc_id: str
        ) -> Optional[User]:

            name = cls.__get_oidc_id_column_name()

            return sess.query(
                cls
            ).filter_by(
                **{name: oidc_id}
            ).one_or_none()

        @classmethod
        def __add(
            cls,
            sess: Session,
            oidc_id: str,
            **oidc_ext
        ) -> User:

            name = cls.__get_oidc_id_column_name()

            new_user = cls(
                **oidc_ext,
                **{name: oidc_id},
            )
            sess.add(new_user)
            sess.commit()

            return new_user

        @classmethod
        def get_or_create(
            cls,
            sess: Session,
            oidc_id: str,
            **oidc_ext
        ) -> User:

            user = cls.__one_or_none(
                sess,
                oidc_id
            )

            if user is not None:
                return user

            return cls.__add(
                sess,
                oidc_id,
                **oidc_ext
            )

        @property
        def role_names(self) -> list[str]:
            names = [
                b.role.name for b in self._role_bindings
            ]
            return sorted(names)

    class _TokenPKMixin:
        """
        Has an integer has a primary key.

        This is all that is needed in most apps,
        and is the default.
        """

        __abstract__ = True

        @declared_attr
        def id(self) -> Mapped[int]:  # noqa A003
            return mapped_column(
                primary_key=True,
                autoincrement=True
            )

    class _EmptyTokenMixin(object):
        """Is deliberately empty"""

    token_pk_mixin_class = (
        _EmptyTokenMixin if token_is_pk else _TokenPKMixin
    )

    class Token(
        AuthToken,
        model_base,
        token_pk_mixin_class,
        token_mixin_class
    ):

        __tablename__ = 'token'

        token: Mapped[str] = mapped_column(
            nullable=False,
            unique=True,
            primary_key=token_is_pk
        )

        created_at: Mapped[datetime] = mapped_column(
            nullable=False,
            default=lambda: datetime.now()
        )
        expires_at: Mapped[datetime] = mapped_column(
            nullable=False,
            default=lambda: datetime.now() + token_expiry_delta
        )

        user_id: Mapped[int] = mapped_column(
            ForeignKey(User.id)
        )

        user = relationship(
            'User',
            back_populates='_tokens',
            foreign_keys=[user_id]
        )

        @classmethod
        def get(
            cls,
            sess: Session,
            token: str
        ) -> Optional[Token]:

            return sess.query(
                cls
            ).filter_by(
                token=token
            ).one_or_none()

        @classmethod
        def get_or_create(
            cls,
            sess: Session,
            token: str,
            user_id: int
        ) -> dict[str, str]:

            token_row = cls.get(
                sess,
                token
            )

            if token_row is None:

                token_row = cls(
                    token=token,
                    user_id=user_id
                )
                sess.add(token_row)
                sess.commit()

            return token_row.__to_dict()

        @classmethod
        def delete(
            cls,
            sess: Session,
            token: str
        ) -> None:

            sess.query(cls).filter_by(token=token).delete()
            sess.commit()

        @classmethod
        def delete_expired(cls, sess: Session) -> None:
            stmt = delete(cls).where(
                cls.expires_at < datetime.now()
            )
            sess.execute(stmt)
            sess.commit()

        def __to_dict(self) -> dict[str, str]:
            return {
                'token_created_at': self.__str_datetime(
                    self.created_at
                ),
                'token_expires_at': self.__str_datetime(
                    self.expires_at
                ),
            }

        def __str_datetime(self, val: datetime) -> str:
            return val.strftime('%Y-%m-%dT%H:%M:%S.%f')

    class Role(
        AuthRole,
        model_base,
        role_mixin_class
    ):

        __tablename__ = 'role'

        id: Mapped[int] = mapped_column(  # noqa A003
            primary_key=True,
            autoincrement=True,
            name=None if not prefix_with_name else 'role_id'
        )

        name: Mapped[str] = mapped_column(
            unique=True
        )

        _role_bindings: Mapped[list['RoleBinding']] = relationship(
            back_populates='role'
        )

    class RoleBinding(AuthRoleBinding, model_base):

        __tablename__ = 'role_binding'

        id: Mapped[int] = mapped_column(  # noqa A003
            primary_key=True,
            autoincrement=True
        )

        user_id: Mapped[int] = mapped_column(
            ForeignKey(User.id)
        )
        role_id: Mapped[int] = mapped_column(
            ForeignKey(Role.id)
        )

        user = relationship(
            'User',
            back_populates='_role_bindings',
            foreign_keys=[user_id]
        )
        role = relationship(
            'Role',
            back_populates='_role_bindings',
            foreign_keys=[role_id]
        )

    return ModelTuple(
        state_class=State,
        token_class=Token,
        user_class=User,
        role_class=Role,
        role_binding_class=RoleBinding
    )
