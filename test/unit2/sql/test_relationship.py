# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.sql.relationship import DefaultSqlRelationshipConfig


class Species:
    @classmethod
    def get_table_name(cls):
        return 'species'

    @classmethod
    def get_to_one_relationship_config(cls):
        return {}

    @classmethod
    def get_to_many_relationship_config(cls):
        return {'all_specimens': 'specimen'}


class Specimen:
    @classmethod
    def get_table_name(cls):
        return 'specimen'

    @classmethod
    def get_to_one_relationship_config(cls):
        return {'og_species': 'species'}

    @classmethod
    def get_to_many_relationship_config(cls):
        return {
            'samples_lul': 'sample',
            'collectors_mine': 'collector'
        }


class Sample:
    @classmethod
    def get_table_name(cls):
        return 'sample'

    @classmethod
    def get_to_one_relationship_config(cls):
        return {'this_specimen_is_mine': 'specimen'}

    @classmethod
    def get_to_many_relationship_config(cls):
        return {}


class Collector:
    @classmethod
    def get_table_name(cls):
        return 'collector'

    @classmethod
    def get_to_one_relationship_config(cls):
        return {'I-collected_this': 'specimen'}

    @classmethod
    def get_to_many_relationship_config(cls):
        return {}


class Irrelevant:
    @classmethod
    def get_table_name(cls):
        return 'nobody_cares'

    @classmethod
    def get_to_one_relationship_config(cls):
        return {}

    @classmethod
    def get_to_many_relationship_config(cls):
        return {}


class TestDefaultSqlRelationshipConfig:
    def test_no_relationships_empty(self):
        """None is returned if all models have no relationships"""

        config = DefaultSqlRelationshipConfig([Irrelevant], lambda t: t.get_table_name())
        assert config.to_dict() is None

    def test_type_function(self):
        """
        The given type function is used correctly, i.e. all tablenames are mapped
        to "DataObject types" using it.
        """

        config = DefaultSqlRelationshipConfig(
            [Sample, Specimen, Species, Collector],
            lambda t: f'{t.get_table_name()}s are the best'
        )
        expected = [
            'collectors are the best',
            'samples are the best',
            'speciess are the best',
            'specimens are the best'
        ]
        observed = config.to_dict()

        assert sorted(observed.keys()) == expected

        # check the relationship tablename maps to a mock object type
        assert observed['samples are the best'].to_one == {
            'this_specimen_is_mine': 'specimens are the best'
        }

    def test_models_without_relationships_eliminated(self):
        """Only models with either kind of relationships are included"""

        config = DefaultSqlRelationshipConfig(
            [Sample, Specimen, Species, Collector, Irrelevant],
            lambda t: t.get_table_name()
        )
        # the Irrelevant model has no relationships, and is hence removed.
        expected = ['collector', 'sample', 'species', 'specimen']
        observed = config.to_dict()
        assert sorted(observed.keys()) == expected

    def test_complex(self):
        """Test lots of models with lots of relationships"""

        config = DefaultSqlRelationshipConfig(
            [Sample, Specimen, Species, Collector],
            lambda t: f'{t.get_table_name()}s'
        )
        # add an s on the end tablename->object_type
        observed = config.to_dict()

        assert observed['samples'].to_one == {
            'this_specimen_is_mine': 'specimens'
        }
        assert observed['samples'].to_many == {}

        assert observed['collectors'].to_one == {
            'I-collected_this': 'specimens'
        }
        assert observed['collectors'].to_many == {}

        assert observed['specimens'].to_one == {
            'og_species': 'speciess'
        }
        assert observed['specimens'].to_many == {
            'samples_lul': 'samples',
            'collectors_mine': 'collectors'
        }

        assert observed['speciess'].to_one == {}
        assert observed['speciess'].to_many == {
            'all_specimens': 'specimens'
        }
