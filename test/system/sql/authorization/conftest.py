# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from unittest.mock import create_autospec

from flask import Flask

import pytest

from sqlalchemy.orm import Session

from tol.core import DataSource, OperableDataSource
from tol.core.operator import Deleter
from tol.sql import model_base
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


def create_test_data(session: Session):
    # Create roles
    admin_role = Role(name='Admin', system_access=True)
    user_role = Role(name='User', system_access=False)
    session.add_all([admin_role, user_role])
    session.flush()  # Ensures IDs are available
    
    # Create users
    admin_user = User(username='admin')
    regular_user = User(username='user')
    session.add_all([admin_user, regular_user])
    session.flush()
    
    # Create memberships
    root_membership = Membership(name='Root Membership')
    child_membership = Membership(name='Child Membership', parent=root_membership)
    session.add_all([root_membership, child_membership])
    session.flush()
    
    # Link users to memberships with roles
    admin_membership = UserMembership(user=admin_user, membership=root_membership, role=admin_role)
    user_membership = UserMembership(user=regular_user, membership=child_membership, role=user_role)
    session.add_all([admin_membership, user_membership])
    session.flush()
    
    # Create a source and data object types
    source = Source(name='Main Source')
    data_type = DataObjectType(name='sample', source=source)
    session.add_all([source, data_type])
    session.flush()
    
    # Create data object type attributes
    attribute1 = DataObjectTypeAttribute(name='project_id', data_object_type=data_type, system=True)
    attribute2 = DataObjectTypeAttribute(name='biosample_id', data_object_type=data_type, system=False)
    session.add_all([attribute1, attribute2])
    session.flush()
    
    # Link memberships to data object types
    membership_data_object = MembershipDataObjectType(membership=root_membership, data_object_type=data_type)
    session.add(membership_data_object)
    session.flush()
    
    # Allow specific attributes for membership data object types
    allowed_attr = MembershipDataObjectTypeAllowedAttribute(
        membership_data_object_type=membership_data_object, data_object_type_attribute=attribute1
    )
    session.add(allowed_attr)
    session.flush()
    
    # Create methods and needs
    read_method = Method(identifier='READ')
    write_method = Method(identifier='WRITE')
    session.add_all([read_method, write_method])
    session.flush()
    
    read_need = Need(data_object_type=data_type)
    session.add(read_need)
    session.flush()
    
    # Associate needs with methods and roles
    need_method_admin = NeedMethod(need=read_need, method=read_method, role=admin_role)
    session.add(need_method_admin)
    session.commit()
