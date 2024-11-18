# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Callable

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
                           pool_pre_ping=True,
                           pool_size=2,
                           max_overflow=10)

    session_maker = sessionmaker(
        bind=engine,
        autoflush=True,
        autocommit=False
    )

    return lambda: session_maker()
