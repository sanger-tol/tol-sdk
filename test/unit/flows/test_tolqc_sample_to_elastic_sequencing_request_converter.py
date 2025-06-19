# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.core import (
    DataObject,
    DataSource,
    core_data_object
)
from tol.core.operator import (
    Relational
)
from tol.core.relationship import RelationshipConfig
from tol.flows.converters import (
    TolqcSampleToElasticSequencingRequestConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['specimen', 'species', 'sample', 'accession']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sample = RelationshipConfig()
        rc_sample.to_one = {
            'specimen': 'specimen',
        }
        rc_specimen = RelationshipConfig()
        rc_specimen.to_one = {
            'species': 'species',
            'accession': 'accession'
        }
        return {'sample': rc_sample,
                'specimen': rc_specimen}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        if source.id == 'id2':
            return source._host.data_object_factory(
                id_='specimen_id2',
                type_='specimen',
                attributes={'supplied_name': 'supplied_name2'}
            )

        if source.id == 'specimen_id3' and relationship_name == 'species':
            return source._host.data_object_factory(
                id_='species_id3',
                type_='species',
                attributes={}
            )

        if source.id == 'specimen_id4' and relationship_name == 'accession':
            return source._host.data_object_factory(
                id_='accession_id4',
                type_='accession',
                attributes={}
            )

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class _MockDataSource(DataSource, Relational):

    @property
    def supported_types(self):
        return ['sequencing_request', 'specimen', 'species', 'tolid']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sequencing_request = RelationshipConfig()
        rc_sequencing_request.to_one = {
            'specimen': 'specimen',
            'tolid': 'tolid',
            'species': 'species'
        }
        return {'sequencing_request': rc_sequencing_request}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        raise NotImplementedError()

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class TestTolqcSampleToElasticSequencingRequestConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSource(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = TolqcSampleToElasticSequencingRequestConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806

        # with no relationships
        obj1 = CoreDataObject(
            id_='id1',
            type_='sample',
            attributes={'hierarchy_name': 'name1',
                        'lims_id': 'lims_id1'}
        )

        # with relationship e.g. specimen
        specimen = CoreDataObject(
            id_='specimen_id2',
            type_='specimen',
            attributes={'supplied_name': 'supplied_name2'},
        )

        obj2 = CoreDataObject(
            id_='id2',
            type_='sample',
            attributes={'hierarchy_name': 'name2',
                        'lims_id': 'lims_id2'},
            to_one={'specimen': specimen}
        )

        # with nested relationship e.g. specimen.species
        species = CoreDataObject(
            id_='species_id3',
            type_='species',
            attributes={
                'taxon_id': 'species_taxonid3'
            }
        )

        specimen3 = CoreDataObject(
            id_='specimen_id3',
            type_='specimen',
            attributes={'supplied_name': 'supplied_name3'},
            to_one={'species': species}
        )

        obj3 = CoreDataObject(
            id_='id3',
            type_='sample',
            attributes={'hierarchy_name': 'name3',
                        'lims_id': 'lims_id3'},
            to_one={'specimen': specimen3}
        )

        # with nested relationship e.g. specimen.accession
        accession = CoreDataObject(
            id_='accession_id4',
            type_='accession',
            attributes={}
        )

        specimen4 = CoreDataObject(
            id_='specimen_id4',
            type_='specimen',
            attributes={'supplied_name': 'supplied_name4'},
            to_one={'accession': accession}
        )

        obj4 = CoreDataObject(
            id_='id4',
            type_='sample',
            attributes={'hierarchy_name': 'name4',
                        'lims_id': 'lims_id4'},
            to_one={'specimen': specimen4}
        )

        # with no relationships
        converteds = converter.convert(obj1)
        ret1 = next(converteds)
        self.assertEqual(obj1.id, ret1.id)
        self.assertEqual('sequencing_request', ret1.type)
        self.assertEqual(ret1.attributes, {
            'hierarchy_name': 'name1',
            'lims_id': 'lims_id1'
        })

        with self.assertRaises(StopIteration):
            next(converteds)

        # with relationship e.g. specimen
        converteds = converter.convert(obj2)
        ret2 = next(converteds)
        self.assertEqual(ret2.attributes, {
            'hierarchy_name': 'name2',
            'lims_id': 'lims_id2'
        })
        assert ret2.tolid.id == 'specimen_id2'
        assert ret2.specimen.id == 'supplied_name2'

        with self.assertRaises(StopIteration):
            next(converteds)

        # with nested relationship e.g. specimen.species
        converteds = converter.convert(obj3)
        ret3 = next(converteds)
        self.assertEqual(ret3.attributes, {
            'hierarchy_name': 'name3',
            'lims_id': 'lims_id3'
        })
        assert ret3.species.id == 'species_taxonid3'
        assert ret3.tolid.id == 'specimen_id3'
        assert ret3.specimen.id == 'supplied_name3'

        with self.assertRaises(StopIteration):
            next(converteds)

        # with nested relationship e.g. specimen.accession
        converteds = converter.convert(obj4)
        ret4 = next(converteds)
        self.assertEqual(ret4.attributes, {
            'hierarchy_name': 'name4',
            'lims_id': 'lims_id4',
            'biospecimen_id': 'accession_id4',
        })
        assert ret4.specimen.id == 'supplied_name4'
        assert ret4.tolid.id == 'specimen_id4'
