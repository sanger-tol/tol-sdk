# SPDX-FileCopyrightText: 2021 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import absolute_import

from tol.api_base.model.base import Base, ExtColumn, db, setup_model
from tol.api_base.model.enum_base import EnumBase
from tol.api_base.model.log_base import LogBase


@setup_model
class AModelRelationship(Base):
    __tablename__ = 'test_a'

    class Meta:
        type_ = 'a'

    # the variable below is necessary on every test model!
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)  # noqa A003
    test_b_rel = db.relationship('BModelRelationship', back_populates='test_a_rel')
    string_column = db.Column(db.String, nullable=True)


@setup_model
class BModelRelationship(Base):
    __tablename__ = 'test_b'

    class Meta:
        type_ = 'b'
        id_column = 'id_string'

    __table_args__ = {'extend_existing': True}
    id_string = db.Column(db.String, primary_key=True)
    a_id = db.Column(db.Integer, db.ForeignKey('test_a.id'), nullable=False)
    test_a_rel = db.relationship(AModelRelationship, back_populates='test_b_rel', foreign_keys=[a_id])
    test_e = db.relationship('EModelRelationship', back_populates='test_b')


@setup_model
class CModelWithNullableColumn(Base):
    __tablename__ = 'test_c'

    class Meta:
        type_ = 'c'

    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)  # noqa A003
    nullable_column = db.Column(db.String, nullable=True)
    other_column = db.Column(db.String, nullable=True)


@setup_model
class DModelWithNonNullableColumn(Base):
    __tablename__ = 'test_d'

    class Meta:
        type_ = 'd'

    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)  # noqa A003
    non_nullable_column = db.Column(db.String, nullable=False)
    other_column = db.Column(db.String, nullable=True)


@setup_model
class EModelRelationship(Base):
    __tablename__ = 'test_e'

    class Meta:
        type_ = 'e'

    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)  # noqa A003
    b_id = db.Column(db.String, db.ForeignKey('test_b.id_string'), nullable=False)
    test_b = db.relationship(BModelRelationship, back_populates='test_e', foreign_keys=[b_id])


@setup_model
class FModelWithExtField(Base):
    __tablename__ = 'test_f'

    class Meta:
        type_ = 'f'

    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)  # noqa A003
    ext = ExtColumn()
    other_column = db.Column(db.String, nullable=True)


@setup_model
class GModelWithFilterableFields(Base):
    __tablename__ = 'test_g'

    class Meta:
        type_ = 'g'

    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)  # noqa A003
    float_column = db.Column(db.Float, nullable=True)
    bool_column = db.Column(db.Boolean, nullable=True)
    datetime_column = db.Column(db.DateTime, nullable=True)
    string_column = db.Column(db.String, nullable=True)


@setup_model
class HModelLog(LogBase):
    __tablename__ = 'test_h'

    class Meta:
        type_ = 'h'

    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)  # noqa A003
    string_column = db.Column(db.String, nullable=True)


@setup_model
class IModelEnum(EnumBase):
    __tablename__ = 'test_i'

    class Meta:
        type_ = 'i'

    __table_args__ = {'extend_existing': True}
    test_j = db.relationship('JModelEnumDependent', back_populates='test_i')


@setup_model
class JModelEnumDependent(Base):
    __tablename__ = 'test_j'

    class Meta:
        type_ = 'j'

    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)  # noqa A003
    i_id = db.Column(db.Integer, db.ForeignKey('test_i.id'), nullable=False)
    test_i = db.relationship(IModelEnum, back_populates='test_j', foreign_keys=[i_id])
