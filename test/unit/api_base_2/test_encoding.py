# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask import Flask
from flask_testing import TestCase

from tol.api_base2 import data_blueprint
from tol.core import DataSource


class TestBlueprintUpdate(TestCase):
    def create_app(self):
        class _MockDataSource(DataSource):
            @property
            def supported_types(self):
                return ['test']

            @property
            def attribute_types(self):
                return {
                    'test': {}
                }

        data_bp = data_blueprint(_MockDataSource({}))
        app = Flask(__name__)
        app.register_blueprint(data_bp)

        return app

    def test_percent_encoding(self):
        pass

