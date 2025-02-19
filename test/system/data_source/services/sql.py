# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os

from flask import Flask

from tol.api_base import data_blueprint
from tol.core.factory import core_data_object
from tol.sql import create_sql_datasource

from ..types import ALL_MODELS


sql_ds = create_sql_datasource(
    ALL_MODELS,
    os.environ['DB_URI']
)
core_data_object(sql_ds)
data_bp = data_blueprint(sql_ds)


app = Flask(__name__)
app.register_blueprint(data_bp)
