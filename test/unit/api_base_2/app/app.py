# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask import Flask

from tol.api_base2 import data_blueprint
from tol.core import DataSource


def _test_application(*data_sources: DataSource) -> Flask:
    app = Flask(__name__)
    app.testing = True
    blueprint = data_blueprint(*data_sources)
    app.register_blueprint(blueprint)

    return app
