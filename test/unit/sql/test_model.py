# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import List
from unittest.mock import MagicMock, PropertyMock

import pytest

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tol.sql import model_base
from tol.sql.exception import BadColumnError
from tol.sql.model import InstanceToManyDict, InstanceToOneDict


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


class Sample(BaseModel):
    __tablename__ = 'sample'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa
    specimen_id_lol: Mapped[str] = mapped_column(
        ForeignKey('specimen.specimen_id')
    )

    # relationship that is not named the same as the table
    original_specimen: Mapped['Specimen'] = relationship(
        back_populates='taken_samples'
    )


class Specimen(BaseModel):
    __tablename__ = 'specimen'

    # id that is not named "id"
    specimen_id: Mapped[str] = mapped_column(primary_key=True)

    # ToLID must be unique
    tolid: Mapped[str] = mapped_column(unique=True)

    taxon_id: Mapped[str] = mapped_column(
        ForeignKey('species.id')
    )

    species: Mapped['Species'] = relationship()
    collectors: Mapped[List['Collector']] = relationship(
        back_populates='collected'
    )

    taken_samples: Mapped[List['Sample']] = relationship(
        back_populates='original_specimen'
    )

    @classmethod
    def get_id_column_name(cls):
        return 'specimen_id'


class Species(BaseModel):
    __tablename__ = 'species'

    id: Mapped[str] = mapped_column(primary_key=True)  # noqa

    specimens: Mapped[List['Specimen']] = relationship(
        back_populates='species'
    )


class Collector(BaseModel):
    __tablename__ = 'collector'

    # id is not named "id"
    email_address: Mapped[str] = mapped_column(primary_key=True)

    # ignore that a collector can only collect one specimen!
    collected_specimen_id: Mapped[str] = mapped_column(
        ForeignKey('specimen.specimen_id')
    )

    collected: Mapped['Specimen'] = relationship(
        back_populates='collectors'
    )

    @classmethod
    def get_id_column_name(cls):
        return 'email_address'


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

    def test_get_column(self):
        """Getting columns that exist"""

        assert _Example.get_column('string_column').key == 'string_column'
        assert _Example.get_column('boolean_column').key == 'boolean_column'
        assert _Example.get_column(
            _Example.get_id_column_name()
        ).key == 'id'
        assert _OverrideId.get_column(
            _OverrideId.get_id_column_name()
        ).key == 'id_other'

    def test_get_column_non_existing(self):
        """Getting columns that don't exist"""

        with pytest.raises(BadColumnError) as e:
            assert _Example.get_column('oh_so_fake')
        assert 'oh_so_fake' in e.value.detail

        with pytest.raises(BadColumnError) as e:
            assert _OverrideId.get_column('yet_still_faker')
        assert 'yet_still_faker' in e.value.detail

    def test_foreign_keys_not_attributes(self):
        """
        Foreign keys and their values, are not included in instance_attributes.
        """

        specimen = Specimen(tolid='mHomSap123', taxon_id='9606')
        assert specimen.instance_attributes == {
            'tolid': 'mHomSap123'
        }

    def test_to_one_relationship_config_non_existing(self):
        """
        Empty dict for to-one relationship config when none are specified.
        """

        assert Species.get_to_one_relationship_config() == {}

    def test_to_one_relationship_config(self):
        """
        All tablenames are present when to-one relationships are configured.
        """

        assert Collector.get_to_one_relationship_config() == {
            'collected': 'specimen'
        }

    def test_to_many_relationship_config_non_existing(self):
        """
        Empty dict for to-many relationship config when none are specified.
        """

        assert Sample.get_to_many_relationship_config() == {}

    def test_to_many_relationship_config(self):
        """
        All tablenames are present when to-many relationships are configured.
        """

        assert Species.get_to_many_relationship_config() == {
            'specimens': 'specimen'
        }

    def test_both_relationship_configs(self):
        """
        All tablenames are present, for both to-one and to-many relationships,
        when both are configured.
        """
        assert Specimen.get_to_one_relationship_config() == {
            'species': 'species'
        }
        assert Specimen.get_to_many_relationship_config() == {
            'collectors': 'collector',
            'taken_samples': 'sample'
        }


class TestRelationDict:
    def test_key_error(self):
        """Bad relationship name -> KeyError"""

        model = MagicMock()
        r = {
            'dont': 'get me!!!',
            'please': 'thank you'
        }
        model.get_to_one_relationship_config.return_value = r
        model.get_to_many_relationship_config.return_value = r
        to_one_dict = InstanceToOneDict(model)
        with pytest.raises(KeyError):
            to_one_dict['nonexistant']
        to_many_dict = InstanceToManyDict(model)
        with pytest.raises(KeyError):
            to_many_dict['faaake']

    def test_good_get(self):
        """Good relationship name -> correct call"""

        model = MagicMock()
        r = {'get': 'irrelevant lol, the target is not fetched!'}
        model.get_to_one_relationship_config.return_value = r
        model.get_to_many_relationship_config.return_value = r
        # it should try to access the attribute 'get' on our model
        type(model).get = PropertyMock(return_value='hype train')
        one_dict = InstanceToOneDict(model)
        assert one_dict['get'] == 'hype train'
        many_dict = InstanceToManyDict(model)
        assert many_dict['get'] == 'hype train'
