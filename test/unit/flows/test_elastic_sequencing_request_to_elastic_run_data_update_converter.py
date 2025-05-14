# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
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
    ElasticSequencingRequestToElasticRunDataUpdateConverter
)


class _MockDataSourceRelational(DataSource, Relational):

    @property
    def supported_types(self):
        return ['sequencing_request', 'sample', 'extraction', 'run_data']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sequencing_request = RelationshipConfig()
        rc_sequencing_request.to_one = {
            'benchling_sample': 'sample',
            'benchling_extraction': 'extraction'
        }
        return {'sequencing_request': rc_sequencing_request}

    def get_to_one_relation(
        self,
        source: DataObject,
        relationship_name: str
    ):
        return None

    def get_to_many_relations(
        self
    ):
        raise NotImplementedError()


class TestElasticSequencingRequestToElasticRunDataUpdateConverter(TestCase):
    def test_convert(self):

        source = _MockDataSourceRelational(config={})
        destination = _MockDataSourceRelational(config={})
        core_data_object(source)
        core_data_object(destination)
        converter = ElasticSequencingRequestToElasticRunDataUpdateConverter(
            data_object_factory=destination.data_object_factory
        )

        CoreDataObject = source.data_object_factory # noqa N806

        sample1 = CoreDataObject('sample', '1234')
        extraction1 = CoreDataObject('extraction', '2345')
        obj1 = CoreDataObject(
            id_='SEQREQ1',
            type_='sequencing_request',
            to_one={
                'benchling_sample': sample1,
                'benchling_extraction': extraction1
            }
        )

        sample2 = CoreDataObject('sample', '5678')
        obj2 = CoreDataObject(
            id_='SEQREQ2',
            type_='sequencing_request',
            to_one={
                'benchling_sample': sample2
            }
        )

        converteds = converter.convert(obj1)
        (id1, ret1) = next(converteds)
        assert id1 is None
        assert ret1['mlwh_sequencing_request.id'] == 'SEQREQ1'
        assert 'benchling_sample' in ret1
        assert ret1['benchling_sample'].id == sample1.id
        assert 'benchling_extraction' in ret1
        assert ret1['benchling_extraction'].id == extraction1.id

        converteds = converter.convert(obj2)
        (id2, ret2) = next(converteds)
        assert id2 is None
        assert ret2['mlwh_sequencing_request.id'] == 'SEQREQ2'
        assert 'benchling_sample' in ret2
        assert ret2['benchling_sample'].id == sample2.id
        assert 'benchling_extraction' not in ret2
