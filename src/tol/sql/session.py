# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable

import flask

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


SessionFactory = Callable[[], Session]


def create_session_factory(db_uri: str) -> SessionFactory:
    """
    Creates a Session factory, i.e. a callable that returns a new
    Session object (each time), given the URI of a database.
    """

    engine = create_engine(db_uri,
                           pool_recycle=1800,
                           pool_pre_ping=True)

    session_maker = sessionmaker(
        bind=engine,
        autoflush=True,
        autocommit=False
    )

    return lambda: session_maker()


def create_flask_session_factory(
    db_uri: str,

    key: str = '_request_session'
) -> SessionFactory:
    """
    Creates a session factory that returns a singleton per
    flask request.
    """

    __factory = create_session_factory(db_uri)

    def session_factory() -> Session:
        existing_session = flask.g.get(key)

        if existing_session is not None:
            return existing_session
        else:
            return flask.g.setdefault(
                key,
                __factory()
            )

    return session_factory
