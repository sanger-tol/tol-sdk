# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from flask import Blueprint, Flask

from flask_testing import TestCase

from tol.api_base import custom_blueprint


class _FlaskTestCase(TestCase, ABC):

    @property
    @abstractmethod
    def _blueprint(self) -> Blueprint:
        pass

    def create_app(self):
        custom_blueprint = self._blueprint
        app = Flask(__name__)
        app.register_blueprint(custom_blueprint)
        return app


class TestCustomBlueprint(_FlaskTestCase):
    def test_good(self):
        response = self.client.open('/bob/good')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        assert response.json == {
            'good': 'job'
        }

    def test_bad(self):
        response = self.client.open('/bob/bad')
        self.assert400(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        assert response.json == {
            'bad': 'idea'
        }

    @property
    def _blueprint(self) -> Blueprint:
        bp = custom_blueprint(
            url_prefix='/bob'
        )

        @bp.route('/good', methods=['GET'])
        def good():
            return {'good': 'job'}, 200

        @bp.route('/bad', methods=['GET'])
        def bad():
            return {'bad': 'idea'}, 400

        return bp
