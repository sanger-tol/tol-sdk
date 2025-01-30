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

from tol.api_base2 import data_blueprint
from tol.api_base2.auth import OidcConfig, require_auth
from tol.core import DataSource, OperableDataSource
from tol.core.operator import DetailGetter, Deleter, OperatorMethod
from tol.sql import create_session_factory
from tol.sql.auth import (
    DbAuthBlueprint,
    ModelTuple,
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
def auth_bp(db_uri, oidc_config, auth_app: Flask):
    bp = db_auth_blueprint(
        BaseModel,
        db_uri,
        auth_app,
        oidc_config_factory=lambda: oidc_config,
        user_mixin_class=TestUserMixin,
        oidc_id_column_name='changed_lol',
        oidc_ext_mapping={
            'do_not_forget_me': 'extra_oidc_field',
            'me_neither': 'extra_oidc_int'
        }
    )
    auth_app.register_blueprint(bp)

    bp.register_authenticator(
        auth_app,
        header_name='Dummy-Token'
    )

    return bp


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


@fixture
def auth_mock_ds() -> OperableDataSource:
    _mock_ds_class = type(
        '',
        (DataSource, Deleter,),
        {}
    )

    mock_ds: OperableDataSource = create_autospec(
        _mock_ds_class,
        spec_set=True
    )
    mock_ds.supported_types = ['sample']
    mock_ds.attribute_types = {'sample': {}}

    return mock_ds


@fixture(autouse=True)
def auth_data_bp(
    auth_app: Flask,
    auth_mock_ds: OperableDataSource
) -> None:

    data_bp = data_blueprint(
        auth_mock_ds,
        url_prefix='/data_auth',
        name='auth_data_source_handler'
    )
    auth_app.register_blueprint(
        data_bp
    )


@fixture(autouse=True)
def test_data(
    auth_bp: DbAuthBlueprint,
    session_factory: SessionFactory,
) -> None:

    auth_models = auth_bp.models

    with session_factory() as session:
        super_admin_role = auth_models.role_class(name='super_admin', system_access=True)
        user_role = auth_models.role_class(name='regular', system_access=False)
        session.add_all([super_admin_role, user_role])
        session.flush()

        super_admin_user = auth_models.user_class(id=1, username='super_admin', changed_lol='super_admin')
        regular_user = auth_models.user_class(id=100, username='regular', changed_lol='regular')
        session.add_all([super_admin_user, regular_user])
        session.flush()

        admin_token = auth_models.token_class(token='super_admin', user_id=1)
        regular_token = auth_models.token_class(token='regular', user_id=100)
        session.add_all([admin_token, regular_token])
        session.flush()

        root_membership = auth_models.membership(name='Root Membership')
        child_membership = auth_models.membership(name='Child Membership', parent=root_membership)
        session.add_all([root_membership, child_membership])
        session.flush()

        admin_membership = auth_models.user_membership(user=super_admin_user, membership=root_membership, role=super_admin_role)
        user_membership = auth_models.user_membership(user=regular_user, membership=child_membership, role=user_role)
        session.add_all([admin_membership, user_membership])
        session.flush()

        source = auth_models.source(name='Main Source')
        data_type = auth_models.data_object_type(name='sample', source=source)
        session.add_all([source, data_type])
        session.flush()

        attribute1 = auth_models.data_object_type_attribute(name='project_id', data_object_type=data_type, system=True)
        attribute2 = auth_models.data_object_type_attribute(name='biosample_id', data_object_type=data_type, system=False)
        session.add_all([attribute1, attribute2])
        session.flush()

        membership_data_object = auth_models.membership_data_object_type(membership=root_membership, data_object_type=data_type)
        session.add(membership_data_object)
        session.flush()

        allowed_attr = auth_models.membership_data_object_type_allowed_attribute(
            membership_data_object_type=membership_data_object, data_object_type_attribute=attribute1
        )
        session.add(allowed_attr)
        session.flush()

        detail_read_method = auth_models.method(
            identifier=OperatorMethod.DETAIL
        )
        detail_delete_method = auth_models.method(
            identifier=OperatorMethod.DELETE
        )
        session.add_all([detail_read_method, detail_delete_method])
        session.flush()
        
        read_need = auth_models.need(data_object_type=data_type)
        session.add(read_need)
        session.flush()

        need_method_admin = auth_models.need_method(need=read_need, method=detail_read_method, role=super_admin_role)
        session.add(need_method_admin)
        session.commit()

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
def auth_app(
    data_bp: Blueprint
) -> Flask:

    app = Flask(__name__)
    app.testing = True

    app.register_blueprint(data_bp)

    app.config['SECRET_KEY'] = "Your_secret_string"
    '''
        This needs to be inplace for Flask-Principle package to interact with the app layer
    '''

    @app.get('/hi')
    @require_auth(role='admin')
    def hi_admin():
        return {'hello': 'world'}, 200

    return app


@fixture(scope='package')
def client(auth_app: Flask):
    return auth_app.test_client()
