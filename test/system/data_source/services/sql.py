# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from flask import Flask

from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError

from tol.api_base2 import data_blueprint
from tol.core.factory import core_data_object
from tol.sql import (
    create_session_factory,
    create_sql_datasource
)

from ..types import ALL_MODELS


DB_URI = os.environ['DB_URI']
session_factory = create_session_factory(DB_URI)


def create_tables():
    engine = create_engine(DB_URI)
    for model in ALL_MODELS:
        try:
            model.__table__.create(engine)
        except ProgrammingError:
            continue


sql_ds = create_sql_datasource(
    ALL_MODELS,
    os.environ['DB_URI']
)
core_data_object(sql_ds)
data_bp = data_blueprint(sql_ds)


app = Flask(__name__)
app.register_blueprint(data_bp)
