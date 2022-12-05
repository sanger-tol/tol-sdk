# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from datetime import datetime, timedelta

from flask import Blueprint, Flask

from flask_restx import Api

from flask_testing import TestCase

import tol.api_base.error.handler as error_handler
from tol.api_base import encoder
from tol.api_base.model import Auth, Role, User, db

from .models import AModelRelationship, BModelRelationship, CModelWithNullableColumn, \
    DModelWithNonNullableColumn, EModelRelationship, FModelWithExtField, \
    GModelWithFilterableFields, HModelLog, IModelEnum, JModelEnumDependent
from .resources import api_a, api_b, api_c, api_d, api_e, api_f, api_g, api_h, api_i, api_j


def _setup_api(blueprint):
    api = Api(
        blueprint,
        doc='/ui',
        title='Tree of Life Testing'
    )
    api.add_namespace(api_a)
    api.add_namespace(api_b)
    api.add_namespace(api_c)
    api.add_namespace(api_d)
    api.add_namespace(api_e)
    api.add_namespace(api_f)
    api.add_namespace(api_g)
    api.add_namespace(api_h)
    api.add_namespace(api_i)
    api.add_namespace(api_j)


class BaseTestCase(TestCase):
    token_1 = 'AnyThingBecAuseThIsIsATEST567890'
    token_2 = 'SomethingElse'

    def _get_auth_user_1_headers(self):
        return {'Authorization': self.token_1}

    def _get_auth_user_2_headers(self):
        return {'Authorization': self.token_2}

    def create_app(self):
        app = Flask(__name__)
        blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
        _setup_api(blueprint)
        app.register_blueprint(blueprint)
        app.register_blueprint(error_handler.blueprint)
        app.json_encoder = encoder.JSONEncoder
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DB_URI']
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['PROPAGATE_EXCEPTIONS'] = True
        db.init_app(app)
        return app

    def _add_model_instance(self, model, **kwargs):
        model(**kwargs).save()

    def add_a(self, **kwargs):
        self._add_model_instance(AModelRelationship, **kwargs)

    def add_b(self, **kwargs):
        self._add_model_instance(BModelRelationship, **kwargs)

    def add_c(self, **kwargs):
        self._add_model_instance(CModelWithNullableColumn, **kwargs)

    def add_d(self, **kwargs):
        self._add_model_instance(DModelWithNonNullableColumn, **kwargs)

    def add_e(self, **kwargs):
        self._add_model_instance(EModelRelationship, **kwargs)

    def add_f(self, **kwargs):
        self._add_model_instance(FModelWithExtField, **kwargs)

    def add_g(self, **kwargs):
        self._add_model_instance(GModelWithFilterableFields, **kwargs)

    def add_h(self, **kwargs):
        self._add_model_instance(HModelLog, **kwargs)

    def add_i(self, **kwargs):
        self._add_model_instance(IModelEnum, **kwargs)

    def add_j(self, **kwargs):
        self._add_model_instance(JModelEnumDependent, **kwargs)

    def setUp(self):
        # general
        self.maxDiff = None
        db.create_all()
        db.session.commit()

        user1 = User(
            id=100,
            name='test_user_admin',
            email='test_user_admin@sanger.ac.uk',
            organisation='Sanger Institute'
        )
        db.session.add(user1)
        role_admin = Role(role='admin')
        role_admin.user = user1
        db.session.add(role_admin)
        auth1 = Auth(
            user_id=100,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=1),
            token=self.token_1
        )
        db.session.add(auth1)

        user2 = User(
            id=101,
            name='test_user_other',
            email='test_user_other@sanger.ac.uk',
            organisation='Sanger Institute'
        )
        db.session.add(user2)
        role_other = Role(role='other')
        role_other.user = user2
        db.session.add(role_other)
        auth2 = Auth(
            user_id=101,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=1),
            token=self.token_2
        )
        db.session.add(auth2)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()

        # test models
        db.session.query(EModelRelationship).delete()
        db.session.query(BModelRelationship).delete()
        db.session.query(AModelRelationship).delete()
        db.session.query(CModelWithNullableColumn).delete()
        db.session.query(DModelWithNonNullableColumn).delete()
        db.session.query(FModelWithExtField).delete()
        db.session.query(GModelWithFilterableFields).delete()
        db.session.query(HModelLog).delete()
        db.session.query(JModelEnumDependent).delete()
        db.session.query(IModelEnum).delete()

        # base models
        db.session.query(Auth).delete()
        db.session.query(Role).delete()
        db.session.query(User).delete()

        db.session.commit()

    def assert201(self, response, *args):
        self.assertEqual(response.status_code, 201)
