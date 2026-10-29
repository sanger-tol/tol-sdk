# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock

import responses

from tol.core import DataObject, core_data_object
from tol.ena import create_ena_datasource

FAKE_API_URL = 'http://fake.lan'
FAKE_ENA_USER = 'user'
FAKE_ENA_PASS = 'pass'
FAKE_ENA_CONTACT = 'contact'
FAKE_ENA_EMAIL = 'email'


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: dict[str, Any] = {}
) -> DataObject:

    data_object = Mock()

    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes

    return data_object


class TestCreateEnaDatasource:
    """larger than unit tests on `create_ena_datasource`"""

    @responses.activate
    def test_get_by_id(self):
        """`create_ena_datasource().get_by_id()`"""

        responses.get(
            f'{FAKE_API_URL}/ena/portal/api/returnFields',
            json=[
                {
                    'columnId': 'tax_id',
                    'description': 'NCBI taxonomic classification',
                    'type': 'taxonomy'
                },
                {
                    'columnId': 'scientific_name',
                    'description': 'Scientific name for an organism',
                    'type': 'text'
                },
                {
                    'columnId': 'common_name',
                    'description': 'Everyday name for an organism',
                    'type': 'text'
                },
            ]
        )

        ena_ds = create_ena_datasource(
            FAKE_API_URL,
            FAKE_ENA_USER,
            FAKE_ENA_PASS,
            FAKE_ENA_CONTACT,
            FAKE_ENA_EMAIL
        )

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='taxon',
            id_='126867',
        )
        mock_do_factory.return_value = mock_data_object
        ena_ds.data_object_factory = mock_do_factory

        in_ = [
            {
                'tax_id': '126867',
                'scientific_name': 'Phalacrocorax aristotelis',
                'common_name': 'European shag',
            }
        ]

        responses.get(
            f'{FAKE_API_URL}/ena/portal/api/search',
            json=in_
        )

        observed = list(ena_ds.get_by_id('taxon', ['126867']))
        mock_do_factory.assert_called_once_with(
            'taxon',
            id_='126867',
            attributes={
                'tax_id': '126867',
                'scientific_name': 'Phalacrocorax aristotelis',
                'common_name': 'European shag',
            }
        )
        assert observed == [mock_data_object]

    @responses.activate
    def test_get_by_id_multiple(self):
        """
        Multiple ids, one of which is not found.
        """
        responses.get(
            f'{FAKE_API_URL}/ena/portal/api/returnFields',
            json=[
                {
                    'columnId': 'tax_id',
                    'description': 'NCBI taxonomic classification',
                    'type': 'taxonomy'
                },
                {
                    'columnId': 'scientific_name',
                    'description': 'Scientific name for an organism',
                    'type': 'text'
                },
                {
                    'columnId': 'common_name',
                    'description': 'Everyday name for an organism',
                    'type': 'text'
                },
            ]
        )

        ena_ds = create_ena_datasource(
            FAKE_API_URL,
            FAKE_ENA_USER,
            FAKE_ENA_PASS,
            FAKE_ENA_CONTACT,
            FAKE_ENA_EMAIL
        )

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='taxon',
            id_='126867',
        )
        mock_do_factory.return_value = mock_data_object
        ena_ds.data_object_factory = mock_do_factory

        in_ = [
            {
                'tax_id': '126867',
                'scientific_name': 'Phalacrocorax aristotelis',
                'common_name': 'European shag',
            }
        ]

        responses.get(
            f'{FAKE_API_URL}/ena/portal/api/search',
            json=in_
        )

        observed = list(
            ena_ds.get_by_id('taxon', ['0', '126867'])
        )

        mock_do_factory.assert_called_once_with(
            'taxon',
            id_='126867',
            attributes={
                'tax_id': '126867',
                'scientific_name': 'Phalacrocorax aristotelis',
                'common_name': 'European shag',
            }
        )
        assert observed == [None, mock_data_object]

    @responses.activate
    def test_relationships_from_api_responses(self):
        """Resolve relationships through the client, converter and parser."""

        fields = [
            'run_accession', 'experiment_accession', 'sample_accession',
            'study_accession', 'tax_id',
        ]
        responses.get(
            f'{FAKE_API_URL}/ena/portal/api/returnFields',
            json=[{'columnId': field, 'type': 'text'} for field in fields],
        )
        run_response = {
            'run_accession': 'ERR123',
            'experiment_accession': 'ERX123',
            'sample_accession': 'SAMEA123',
            'study_accession': 'PRJEB123',
            'tax_id': '9606',
        }
        records = {
            'read_run': run_response,
            'read_experiment': {
                'experiment_accession': 'ERX123',
                'sample_accession': 'SAMEA123',
                'study_accession': 'PRJEB123',
            },
            'sample': {'sample_accession': 'SAMEA123', 'tax_id': '9606'},
            'study': {'study_accession': 'PRJEB123'},
            'taxon': {'tax_id': '9606'},
        }
        for object_type, record in records.items():
            responses.get(
                f'{FAKE_API_URL}/ena/portal/api/search',
                json=[record],
                match=[responses.matchers.query_param_matcher(
                    {'result': object_type}, strict_match=False
                )],
            )
        ena_ds = create_ena_datasource(
            FAKE_API_URL,
            FAKE_ENA_USER,
            FAKE_ENA_PASS,
            FAKE_ENA_CONTACT,
            FAKE_ENA_EMAIL
        )
        core_data_object(ena_ds)

        run = ena_ds.get_one('read_run', 'ERR123')

        assert run.sample.id == 'SAMEA123'
        assert run.study.id == 'PRJEB123'
        assert run.taxon.id == '9606'
        assert run.experiment.id == 'ERX123'
        assert run.experiment.sample.id == 'SAMEA123'
        assert run.experiment.study.id == 'PRJEB123'
        assert run.sample.taxon.id == '9606'
        assert [obj.id for obj in run.experiment.runs] == ['ERR123']
        assert [obj.id for obj in run.sample.experiments] == ['ERX123']
        assert [obj.id for obj in run.study.experiments] == ['ERX123']

    @responses.activate
    def test_assembly_provenance_from_api_responses(self):
        """Resolve explicit assembly inputs and preserve sequencing metadata."""

        assembly_id = 'GCA_922984935.2'
        fields = [
            'assembly_set_accession', 'assembly_accession', 'run_accession',
            'sample_accession', 'study_accession', 'tax_id',
            'instrument_platform', 'library_strategy', 'library_name',
            'library_construction_protocol',
        ]
        responses.get(
            f'{FAKE_API_URL}/ena/portal/api/returnFields',
            json=[{'columnId': field, 'type': 'text'} for field in fields],
        )
        records = {
            'assembly': [{
                'assembly_accession': 'GCA_922984935',
                'assembly_set_accession': assembly_id,
                'run_accession': 'ERR6688402;ERR6939248;ERR6688402',
                'sample_accession': 'SAMEA7524400',
                'study_accession': 'PRJEB49353',
                'tax_id': '9662',
            }],
            'read_run': [{
                'run_accession': 'ERR6688402',
                'sample_accession': 'SAMEA7524440',
                'instrument_platform': 'ILLUMINA',
                'library_strategy': 'Hi-C',
                'library_name': '',
                'library_construction_protocol': 'Hi-C - Arima v2',
            }, {
                'run_accession': 'ERR6939248',
                'sample_accession': 'SAMEA7524400',
                'instrument_platform': 'PACBIO_SMRT',
                'library_strategy': 'WGS',
            }],
            'sample': [{'sample_accession': 'SAMEA7524440'}],
            'study': [{'study_accession': 'PRJEB49353'}],
            'taxon': [{'tax_id': '9662'}],
        }
        for object_type, values in records.items():
            params = {'result': object_type}
            if object_type == 'read_run':
                params['query'] = (
                    'run_accession= "ERR6688402" OR run_accession= "ERR6939248" '
                )
            responses.get(
                f'{FAKE_API_URL}/ena/portal/api/search',
                json=values,
                match=[responses.matchers.query_param_matcher(
                    params, strict_match=False
                )],
            )
        ena_ds = create_ena_datasource(
            FAKE_API_URL,
            FAKE_ENA_USER,
            FAKE_ENA_PASS,
            FAKE_ENA_CONTACT,
            FAKE_ENA_EMAIL
        )
        core_data_object(ena_ds)

        assembly = ena_ds.get_one('assembly', assembly_id)
        runs = list(assembly.runs)
        run_requests = [
            call.request for call in responses.calls
            if '/search?' in call.request.url and 'result=read_run' in call.request.url
        ]
        assert len(run_requests) == 1

        assert assembly.type == 'assembly'
        assert assembly.id == assembly_id
        assert [run.type for run in runs] == ['read_run', 'read_run']
        assert [run.id for run in runs] == ['ERR6688402', 'ERR6939248']
        assert runs[0].sample.type == 'sample'
        assert runs[0].sample.id == 'SAMEA7524440'
        assert runs[0].sample.id != assembly.sample_accession
        assert runs[0].instrument_platform == 'ILLUMINA'
        assert runs[0].library_strategy == 'Hi-C'
        assert runs[0].library_name == ''
        assert runs[0].library_construction_protocol == 'Hi-C - Arima v2'
        assert assembly.study.type == 'study'
        assert assembly.study.id == 'PRJEB49353'
        assert assembly.taxon.type == 'taxon'
        assert assembly.taxon.id == '9662'

        # Pagination still uses the converted assembly IDs and counts.
        page, total = ena_ds.get_list_page('assembly', page_number=1, page_size=1)
        assert [obj.id for obj in page] == [assembly_id]
        assert total == 1
        page, total = ena_ds.get_list_page('assembly', page_number=2, page_size=1)
        assert page == []
        assert total == 1
