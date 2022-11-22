# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime, timedelta
import os

from flask import Flask, Blueprint
from flask_testing import TestCase
from flask_restx import Api

from tol.api_base import encoder
from tol.api_base.model import db, User, Role, Auth

from .models import A_ModelRelationship, \
                    B_ModelRelationship, \
                    C_ModelWithNullableColumn, \
                    D_ModelWithNonNullableColumn, \
                    E_ModelRelationship, \
                    F_ModelWithExtField, \
                    G_ModelWithFilterableFields, \
                    H_ModelLog, \
                    I_ModelEnum, \
                    J_ModelEnumDependent
from .resources import api_A, api_B, api_C, api_D, \
                                api_E, api_F, api_G, api_H, \
                                api_I, api_J


def _setup_api(blueprint):
    api = Api(
        blueprint,
        doc='/ui',
        title="Tree of Life Quality Control"
    )
    api.add_namespace(api_A)
    api.add_namespace(api_B)
    api.add_namespace(api_C)
    api.add_namespace(api_D)
    api.add_namespace(api_E)
    api.add_namespace(api_F)
    api.add_namespace(api_G)
    api.add_namespace(api_H)
    api.add_namespace(api_I)
    api.add_namespace(api_J)


class BaseTestCase(TestCase):
    token_1 = "AnyThingBecAuseThIsIsATEST567890"
    token_2 = "SomethingElse"

    def _get_auth_user_1_headers(self):
        return {"Authorization": self.token_1}

    def _get_auth_user_2_headers(self):
        return {"Authorization": self.token_2}

    def create_app(self):
        app = Flask(__name__)
        blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
        _setup_api(blueprint)
        app.register_blueprint(blueprint)
        app.json_encoder = encoder.JSONEncoder
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URI']
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        return app

    def _add_model_instance(self, model, **kwargs):
        model(**kwargs).save()

    def add_A(self, **kwargs):
        self._add_model_instance(A_ModelRelationship, **kwargs)

    def add_B(self, **kwargs):
        self._add_model_instance(B_ModelRelationship, **kwargs)

    def add_C(self, **kwargs):
        self._add_model_instance(C_ModelWithNullableColumn, **kwargs)

    def add_D(self, **kwargs):
        self._add_model_instance(D_ModelWithNonNullableColumn, **kwargs)

    def add_E(self, **kwargs):
        self._add_model_instance(E_ModelRelationship, **kwargs)

    def add_F(self, **kwargs):
        self._add_model_instance(F_ModelWithExtField, **kwargs)

    def add_G(self, **kwargs):
        self._add_model_instance(G_ModelWithFilterableFields, **kwargs)

    def add_H(self, **kwargs):
        self._add_model_instance(H_ModelLog, **kwargs)

    def add_I(self, **kwargs):
        self._add_model_instance(I_ModelEnum, **kwargs)

    def add_J(self, **kwargs):
        self._add_model_instance(J_ModelEnumDependent, **kwargs)

    def setUp(self):
        # general
        self.maxDiff = None
        db.create_all()
        db.session.commit()

        user1 = User(
            id=100,
            name="test_user_admin",
            email="test_user_admin@sanger.ac.uk",
            organisation="Sanger Institute"
        )
        db.session.add(user1)
        role_admin = Role(role="admin")
        role_admin.user = user1
        db.session.add(role_admin)
        auth1 = Auth(
            user_id=100,
            created_at=datetime.now(),
            expires_at=datetime.now()+timedelta(days=1),
            token=self.token_1
        )
        db.session.add(auth1)

        user2 = User(
            id=101,
            name="test_user_other",
            email="test_user_other@sanger.ac.uk",
            organisation="Sanger Institute"
        )
        db.session.add(user2)
        role_other = Role(role="other")
        role_other.user = user2
        db.session.add(role_other)
        auth2 = Auth(
            user_id=101,
            created_at=datetime.now(),
            expires_at=datetime.now()+timedelta(days=1),
            token=self.token_2
        )
        db.session.add(auth2)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()

        # test models
        db.session.query(E_ModelRelationship).delete()
        db.session.query(B_ModelRelationship).delete()
        db.session.query(A_ModelRelationship).delete()
        db.session.query(C_ModelWithNullableColumn).delete()
        db.session.query(D_ModelWithNonNullableColumn).delete()
        db.session.query(F_ModelWithExtField).delete()
        db.session.query(G_ModelWithFilterableFields).delete()
        db.session.query(H_ModelLog).delete()
        db.session.query(J_ModelEnumDependent).delete()
        db.session.query(I_ModelEnum).delete()

        # base models
        db.session.query(Auth).delete()
        db.session.query(Role).delete()
        db.session.query(User).delete()

        db.session.commit()

    def assert201(self, response, *args):
        self.assertEqual(response.status_code, 201)
