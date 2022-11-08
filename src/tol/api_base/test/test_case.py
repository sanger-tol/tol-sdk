# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from flask_testing import TestCase as FlaskTestCase

from main.model import db, Role, User

from test.models import A_ModelRelationship, B_ModelRelationship, \
                             C_ModelWithNullableColumn, \
                             D_ModelWithNonNullableColumn, \
                             E_ModelRelationship, F_ModelWithExtField, \
                             G_ModelWithFilterableFields, \
                             H_ModelLog, I_ModelEnum, J_ModelEnumDependent


class TestCase(FlaskTestCase):

    api_key_1 = "AnyThingBecAuseThIsIsATEST567890"
    api_key_2 = "SomethingElse"

    def setUp(self):
        # general
        self.maxDiff = None
        db.create_all()
        db.session.commit()

        # ToLQC tests
        user1 = User(id=100,
                          name="test_user_admin",
                          email="test_user_admin@sanger.ac.uk",
                          organisation="Sanger Institute",
                          api_key=self.api_key_1)
        db.session.add(user1)
        role_admin = Role(role="admin")
        role_admin.user = user1
        db.session.add(role_admin)

        user2 = User(id=101,
                          name="test_user_other",
                          email="test_user_other@sanger.ac.uk",
                          organisation="Sanger Institute",
                          api_key=self.api_key_2)
        db.session.add(user2)
        role_other = Role(role="other")
        role_other.user = user2
        db.session.add(role_other)

    def tearDown(self):
        db.session.rollback()

        # base models
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

        # Main models
        db.session.query(Role).delete()
        db.session.query(User).delete()
        db.session.commit()

    def assert201(self, response, *args):
        self.assertEqual(response.status_code, 201)
