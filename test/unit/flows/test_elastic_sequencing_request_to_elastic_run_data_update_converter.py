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
        return ['sequencing_request', 'sample', 'extraction', 'extraction_container', 'run_data']

    @property
    def attribute_types(self):
        raise NotImplementedError()

    @property
    def relationship_config(self):
        rc_sequencing_request = RelationshipConfig()
        rc_sequencing_request.to_one = {
            'sample': 'sample',
            'extraction': 'extraction',
            'extraction_container': 'extraction_container'
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
            data_object_factory=destination.data_object_factory,
            config=ElasticSequencingRequestToElasticRunDataUpdateConverter.Config()
        )

        CoreDataObject = source.data_object_factory # noqa N806

        sample1 = CoreDataObject('sample', '1234')
        extraction1 = CoreDataObject('extraction', '2345')
        extraction_container1 = CoreDataObject('extraction_container', '3456')
        obj1 = CoreDataObject(
            id_='SEQREQ1',
            type_='sequencing_request',
            to_one={
                'sample': sample1,
                'extraction': extraction1,
                'extraction_container': extraction_container1
            }
        )

        sample2 = CoreDataObject('sample', '5678')
        obj2 = CoreDataObject(
            id_='SEQREQ2',
            type_='sequencing_request',
            to_one={
                'sample': sample2
            }
        )

        converteds = converter.convert(obj1)
        (id1, ret1) = next(converteds)
        assert id1 is None
        assert ret1['sequencing_request.id'] == 'SEQREQ1'
        assert 'sample' in ret1
        assert ret1['sample'].id == sample1.id
        assert 'extraction' in ret1
        assert ret1['extraction'].id == extraction1.id
        assert 'extraction_container' in ret1
        assert ret1['extraction_container'].id == extraction_container1.id

        converteds = converter.convert(obj2)
        (id2, ret2) = next(converteds)
        assert id2 is None
        assert ret2['sequencing_request.id'] == 'SEQREQ2'
        assert 'sample' in ret2
        assert ret2['sample'].id == sample2.id
        assert 'extraction' not in ret2
        assert 'extraction_container' not in ret2
