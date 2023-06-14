# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from sqlalchemy import Boolean, Column, Integer, String

from tol.sql import model_base


BaseModel = model_base()


class _Example(BaseModel):
    __tablename__ = 'example'

    # this is not how things are declared in other apps,
    # but should correspond to them anyway
    id = Column(Integer, primary_key=True)  # noqa
    string_column = Column(String, default='lol')
    boolean_column = Column(Boolean, nullable=False)

    def __init__(self) -> None:
        self.id = 9092
        self.boolean_column = True
        self.string_column = 'not funny'


class _OverrideId(BaseModel):

    __tablename__ = 'yet-another-example'

    id_other = Column(String, primary_key=True)
    string_column = Column(String, default='lol')
    boolean_column = Column(Boolean, nullable=False)

    def __init__(self) -> None:
        self.id_other = 'this-one-is-mine'
        self.boolean_column = True
        self.string_column = 'there are many like it'

    @classmethod
    def get_id_column_name(cls) -> str:
        return 'id_other'


class TestDefaultModel:
    def test_id_non_string(self):
        """A non-string id converts to string"""
        assert _Example().instance_id == '9092'

    def test_tablename(self):
        """Tablename is fetched from __tablename__"""
        assert _Example.get_table_name() == 'example'

    def test_attributes(self):
        """Attributes are determined correctly"""
        assert _Example().instance_attributes == {
            'boolean_column': True,
            'string_column': 'not funny'
        }

    def test_override_id(self):
        """
        Attributes and id are determined correctly when id is overriden
        """

        instance = _OverrideId()
        assert instance.instance_id == 'this-one-is-mine'
        assert instance.instance_attributes == {
            'boolean_column': True,
            'string_column': 'there are many like it'
        }
