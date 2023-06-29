# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod

from flask import Blueprint, Flask

from flask_testing import TestCase

from tol.api_base2 import system_blueprint


class _FlaskTestCase(TestCase, ABC):

    @property
    @abstractmethod
    def _blueprint(self) -> Blueprint:
        pass

    def create_app(self):
        system_blueprint = self._blueprint
        app = Flask(__name__)
        app.register_blueprint(system_blueprint)
        return app


class TestSystemBlueprint1(_FlaskTestCase):
    def test_get_environment_default(self):
        """setting $ENVIRONMENT -> returned on /environment"""

        response = self.client.open('/system/environment')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        assert response.json == {
            'environment': 'an environment'
        }

    def test_get_healthz_default(self):
        """/healthz on default prefix"""

        response = self.client.open('/system/healthz')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    @property
    def _blueprint(self) -> Blueprint:
        return system_blueprint(
            env_vars={'ENVIRONMENT': 'an environment'}
        )


class TestSystemBlueprint2(_FlaskTestCase):

    def test_custom_environment_keys(self):
        """overriding environment_keys -> all returned /environment"""

        response = self.client.open('/system/environment')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        assert response.json == {
            'hype': 'train',
            'such like': 'indeed'
        }

    @property
    def _blueprint(self) -> Blueprint:
        return system_blueprint(
            env_map={
                'hype': 'HYPE',
                'such like': 'yes'
            },
            env_vars={
                'ENVIRONMENT': 'an environment',
                'HYPE': 'train',
                'yes': 'indeed',
                'no': 'I think not!'
            }
        )


class TestSystemBlueprint3(_FlaskTestCase):
    def test_get_envrionment_custom_prefix(self):
        """overriding prefix -> environment served here"""

        response = self.client.open('/lollll/environment')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )
        assert response.json == {
            'environment': 'an environment'
        }

    def test_get_healthz_custom_prefix(self):
        """/healthz on custom prefix"""

        response = self.client.open('/lollll/healthz')
        self.assert200(
            response,
            f'Response body is : {response.data.decode("utf-8")}'
        )

    @property
    def _blueprint(self) -> Blueprint:
        return system_blueprint(
            url_prefix='/lollll',
            env_vars={'ENVIRONMENT': 'an environment'}
        )
