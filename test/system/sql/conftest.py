# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from typing import Any, Iterable
from unittest.mock import create_autospec

from flask import Blueprint, Flask

from pytest import fixture

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from tol.api_base import data_blueprint
from tol.api_base.auth import OidcConfig, require_auth
from tol.core import DataSource
from tol.core.operator import DetailGetter
from tol.sql import create_session_factory
from tol.sql.auth import (
    DbAuthBlueprint,
    db_auth_blueprint,
)
from tol.sql.session import SessionFactory

from .models import TestUserMixin, create_models_list
from .models.base import BaseModel


def __set_up(db_uri: str) -> None:
    engine = create_engine(db_uri)
    BaseModel.metadata.create_all(engine)


def __tear_down(
    session_factory: SessionFactory,
    models: Iterable[type[Any]]
) -> None:
    session = session_factory()
    for model in models:
        session.execute(
            delete(model)
        )
    session.commit()


@fixture(scope='package')
def db_uri() -> str:
    return os.environ['DB_URI']


@fixture(scope='package')
def oidc_config() -> OidcConfig:
    return OidcConfig(
        auth_url='http://local.lan/authorize',
        user_info_url='http://local.lan/userinfo',
        token_url='http://local.lan/token',
        revoke_url='http://local.lan/revoke',
        client_id='a fun ID',
        client_secret='bubbles',
        redirect_uri='http://other.lan/callback'
    )


@fixture(scope='package')
def auth_bp(db_uri, oidc_config):
    return db_auth_blueprint(
        BaseModel,
        db_uri,
        oidc_config_factory=lambda: oidc_config,
        user_mixin_class=TestUserMixin,
        oidc_id_column_name='changed_lol',
        oidc_ext_mapping={
            'do_not_forget_me': 'extra_oidc_field',
            'me_neither': 'extra_oidc_int'
        }
    )


@fixture(scope='package')
def full_models_list(auth_bp: DbAuthBlueprint):

    return [
        *auth_bp.models,
        *create_models_list,
    ]


@fixture(scope='package')
def models_list(full_models_list):
    """only those relevant to `SqlDataSource`."""

    return [
        m for m in full_models_list
        if not m.__tablename__.startswith('oidc_')
    ]


@fixture(autouse=True)
def session_factory(db_uri: str, full_models_list: list[type[Any]]):

    __set_up(db_uri)

    __session_factory = create_session_factory(db_uri)

    yield __session_factory

    __tear_down(
        __session_factory,
        reversed(full_models_list)
    )


@fixture(scope='function')
def sess(
    session_factory: SessionFactory
) -> Session:

    sess = session_factory()

    yield sess

    sess.close()


@fixture(scope='package')
def data_source():

    class _MockDataSource(DataSource, DetailGetter):
        pass

    mock_ds = create_autospec(_MockDataSource, spec_set=True)
    mock_ds.supported_types = ['test']
    mock_ds.get_by_id.return_value = []

    return mock_ds


@fixture(scope='package')
def data_bp(data_source: DataSource):
    return data_blueprint(
        data_source
    )


@fixture(scope='package')
def app(
    auth_bp: DbAuthBlueprint,
    data_bp: Blueprint
) -> Flask:

    app = Flask(__name__)
    app.testing = True

    app.register_blueprint(auth_bp)
    app.register_blueprint(data_bp)

    @app.get('/hi')
    @require_auth(role='admin')
    def hi_admin():
        return {'hello': 'world'}, 200

    auth_bp.register_authenticator(
        app,
        header_name='Dummy-Token'
    )

    return app


@fixture(scope='package')
def client(app: Flask):
    return app.test_client()
