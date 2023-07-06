# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import logging
import os
from unittest import TestCase

from sqlalchemy import create_engine, delete
from sqlalchemy.exc import ProgrammingError

from tol.sql import create_session_factory

from .models import create_models_list, delete_models_list


db_uri = os.environ['DB_URI']

session_factory = create_session_factory(db_uri)

models_list = create_models_list


class DatabaseTestCase(TestCase):
    """Setups and tears down a database before/after each test"""

    def setUp(self) -> None:
        engine = create_engine(db_uri)
        for model in create_models_list:
            try:
                model.__table__.create(engine)
            except ProgrammingError as e:
                logging.info(e)

    def tearDown(self) -> None:
        session = session_factory()
        for model in delete_models_list:
            session.execute(
                delete(model)
            )
        session.commit()
