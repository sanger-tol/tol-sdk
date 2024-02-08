# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, NamedTuple, Optional
from uuid import uuid4

from sqlalchemy import ForeignKey, delete, select
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

    oidc_id: str

    _tokens: list[AuthToken]

    @classmethod
    @abstractmethod
    def get_or_create(
        cls,
        sess: Session,
        oidc_id: str
    ) -> AuthUser:
        """
        Adds a new `User` row to the DB, with the
        given `oidc_id`, if it doesn't already exist.

        Returns the found row if it does.
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
    def register(
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


class ModelTuple(NamedTuple):
    """
    Contains the `ModelClass` variables required
    for OIDC in a database.
    """

    state_class: type[AuthState]
    user_class: type[AuthUser]
    token_class: type[AuthToken]


def create_models(
    model_base: ModelClass,
    user_table_name: str,
    user_mixin_class: ModelClass,
    token_expiry_delta: timedelta
) -> ModelTuple:
    """
    Creates the OIDC db models, given a suitable base (and
    the name of the `User` model.)

    Returns a `NamedTuple`.
    """

    class State(AuthState, model_base):

        __tablename__ = 'oidc_state'

        id: Mapped[str] = mapped_column(  # noqa A003
            primary_key=True
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

    class User(AuthUser, model_base, user_mixin_class):

        __tablename__ = user_table_name

        id: Mapped[int] = mapped_column(  # noqa A003
            primary_key=True,
            autoincrement=True
        )

        oidc_id: Mapped[str] = mapped_column(
            unique=True,
            nullable=False
        )

        _tokens: Mapped[list['Token']] = relationship(
            back_populates='user'
        )

        @classmethod
        def __one_or_none(
            cls,
            sess: Session,
            oidc_id: str
        ) -> Optional[User]:

            return sess.query(
                cls
            ).filter_by(
                oidc_id=oidc_id
            ).one_or_none()

        @classmethod
        def __add(
            cls,
            sess: Session,
            oidc_id: str
        ) -> User:

            new_user = cls(oidc_id=oidc_id)
            sess.add(new_user)
            sess.commit()

            return new_user

        @classmethod
        def get_or_create(
            cls,
            sess: Session,
            oidc_id: str
        ) -> User:

            user = cls.__one_or_none(
                sess,
                oidc_id
            )

            if user is not None:
                return user

            return cls.__add(
                sess,
                oidc_id
            )

    class Token(AuthToken, model_base):

        __tablename__ = 'oidc_token'

        id: Mapped[int] = mapped_column(  # noqa A003
            primary_key=True
        )

        token: Mapped[str] = mapped_column(
            nullable=False,
            unique=True
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
        def register(
            cls,
            sess: Session,
            token: str,
            user_id: int
        ) -> dict[str, str]:

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

    return ModelTuple(
        state_class=State,
        token_class=Token,
        user_class=User
    )
