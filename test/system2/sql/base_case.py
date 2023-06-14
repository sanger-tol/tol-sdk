# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging
import os
from unittest import TestCase

from sqlalchemy import create_engine, delete
from sqlalchemy.exc import ProgrammingError

from tol.sql import create_session_factory

from . import models


db_uri = os.environ['DB_URI']

session_factory = create_session_factory(db_uri)


models_list = [
    models.A
]


class DatabaseTestCase(TestCase):
    """Setups and tears down a database before/after each test"""

    def setUp(self) -> None:
        engine = create_engine(db_uri)
        for model in models_list:
            try:
                model.__table__.create(engine)
            except ProgrammingError as e:
                logging.info(e)

    def tearDown(self) -> None:
        session = session_factory()
        for model in models_list:
            session.execute(
                delete(model)
            )
        session.commit()
