# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from unittest.mock import create_autospec

from flask import Flask

import pytest

from tol.core import DataSource, OperableDataSource
from tol.core.operator import Deleter, OperatorMethod
from tol.sql import model_base
from tol.sql.session import SessionFactory
from tol.sql.auth import ModelTuple, db_auth_blueprint
from tol.sql.auth.blueprint import DbAuthBlueprint


@pytest.fixture(scope='package')
def db_uri() -> str:
    return os.environ['DB_URI']


@pytest.fixture
def base_model() -> type:
    return model_base()


@pytest.fixture
def auth_app() -> Flask:
    flask_app = Flask(__name__)
    flask_app.testing = True

    return flask_app


@pytest.fixture
def db_auth_bp(
    base_model: type,
    db_uri: str,
    auth_app: Flask
) -> DbAuthBlueprint:

    auth_bp = db_auth_blueprint(
        base_model,
        db_uri,
        auth_app
    )
    auth_app.register_blueprint(auth_bp)
    auth_bp.register_authenticator(auth_app)

    return auth_bp


@pytest.fixture
def auth_models(
    db_auth_bp: DbAuthBlueprint
) -> ModelTuple:

    return db_auth_bp.models


@pytest.fixture
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


@pytest.fixture(autouse=True)
def test_data(
    auth_models: ModelTuple,
    session_factory: SessionFactory,
) -> None:

    with session_factory() as session:
        admin_role = auth_models.role_class(name='Admin', system_access=True)
        user_role = auth_models.role_class(name='auth_models.user_class', system_access=False)
        session.add_all([admin_role, user_role])
        session.flush()

        admin_user = auth_models.user_class(username='admin')
        regular_user = auth_models.user_class(username='user')
        session.add_all([admin_user, regular_user])
        session.flush()

        root_membership = auth_models.membership(name='Root Membership')
        child_membership = auth_models.membership(name='Child Membership', parent=root_membership)
        session.add_all([root_membership, child_membership])
        session.flush()

        admin_membership = auth_models.user_membership(user=admin_user, membership=root_membership, role=admin_role)
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

        need_method_admin = auth_models.need_method(need=read_need, method=detail_read_method, role=admin_role)
        session.add(need_method_admin)
        session.commit()
