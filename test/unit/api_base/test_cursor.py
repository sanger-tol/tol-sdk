# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from flask import Flask
from flask.testing import FlaskClient

import pytest

from tol.api_base import data_blueprint
from tol.core import DataObject, DataSource
from tol.core.operator import Cursor


class CursorDS(DataSource, Cursor):
    pass


@pytest.fixture
def cursor_ds() -> CursorDS:
    ds = create_autospec(
        CursorDS,
        spec_set=True
    )
    ds.supported_types = ['test']

    return ds


@pytest.fixture
def app(cursor_ds: CursorDS) -> Flask:
    app = Flask(__name__)
    data_bp = data_blueprint(
        cursor_ds
    )
    app.register_blueprint(data_bp)
    app.testing = True

    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


class TestCursor:
    """
    Giving an instance that implements `Cursor`
    to `data_blueprint`.
    """

    def test_none_found(
        self,
        cursor_ds: CursorDS,
        client: FlaskClient
    ):
        """
        Instance doesn't find anything
        (i.e. returns `([], None)`) ->
        do likewise.
        """

        cursor_ds.get_cursor_page.return_value = ([], None)

        r = client.post(
            '/data/test:cursor',
            json={}
        )
        assert r.status_code == 200, r.text

        expected = {
            'data': [],
            'meta': {
                'search_after': None
            }
        }

        assert r.json == expected

    def test_populated(
        self,
        cursor_ds: CursorDS,
        client: FlaskClient
    ):
        """
        Instances returns a populated "answer":

        - `list[DataObject]` under the `data` key
        - `list[str]` `search_after` under the
          `meta` key
        """

        cursor_ds.get_cursor_page.return_value = (
            [self.__mock_obj()],
            ['10']
        )

        r = client.post(
            '/data/test:cursor',
            json={}
        )

        expected = {
            'data': [
                {
                    'type': 'test',
                    'id': '10',
                    'attributes': {
                        'testing': True,
                        'sure': 'absolutely'
                    }
                }
            ],
            'meta': {
                'search_after': ['10']
            }
        }

        assert r.json == expected

    def __mock_obj(self) -> DataObject:
        obj = create_autospec(
            DataObject,
            spec_set=True
        )

        obj.type = 'test'
        obj.id = '10'
        obj.attributes = {
            'testing': True,
            'sure': 'absolutely'
        }

        return obj
