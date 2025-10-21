# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json

import responses

from tol.bold.client import BoldApiClient


FAKE_API_URL = 'http://test.lan/api'
FAKE_API_KEY = 'key'


class TestBoldApiClient:
    """The `BoldApiClient` and its methods"""

    @responses.activate
    def test_get_detail_data(self):
        """Default values, no token"""

        client = BoldApiClient(FAKE_API_URL, FAKE_API_URL, FAKE_API_KEY)
        objs = [
            {
                'processid': f'PROCESS{i}',
                'record_id': f'RECORD{i}',
                'insdc_acs': f'INSDC{i}',
                'sampleid': f'SAMPLE{i}',
                'specimenid': 1234 + i,
                'taxid': 3456 + i,
                'short_note': f'NOTE{i}',
                'identification_method': f'IDENT{i}',
                'museumid': f'MUSEUM{i}',
                'fieldid': f'FIELD{i}',
                'collection_code': f'COLLECT{i}',
                'processid_minted_date': f'2023-01-0{i}',
                'inst': f'INST{i}',
                'funding_src': f'FUNDING{i}',
                'sex': f'SEX{i}',
                'life_stage': f'LIFESTAGE{i}',
                'reproduction': f'REPRO{i}',
                'habitat': f'HABITAT{i}',
                'collectors': f'COLLECTORS{i}',
                'site_code': f'SITE{i}',
                'specimen_linkout': f'LINKOUT{i}',
                'collection_event_id': f'EVENT{i}',
                'sampling_protocol': f'PROTOCOL{i}',
                'tissue_type': f'TISSUE{i}',
                'collection_date_start': f'2023-02-0{i}',
                'collection_time': f'12:13:1{i}',
                'associated_taxa': f'TAXA{i}',
                'associated_specimens': f'SPECIMENS{i}',
                'voucher_type': f'VOUCHER{i}',
                'notes': f'NOTES{i}',
                'taxonomy_notes': f'TAXONOMY{i}',
                'collection_notes': f'COLLECT{i}',
                'geoid': 123 + i,
                'marker_code': f'MARKER{i}',
                'kingdom': f'KINGDOM{i}',
                'phylum': f'PHYLUM{i}',
                'class': f'CLASS{i}',
                'order': f'ORDER{i}',
                'family': f'FAMILY{i}',
                'subfamily': f'SUBFAMILY{i}',
                'tribe': f'TRIBE{i}',
                'genus': f'GENUS{i}',
                'species': f'SPECIES{i}',
                'subspecies': f'SUBSPECIES{i}',
                'taxon_name': f'TAXONNAME{i}',
                'taxon_rank': f'TAXONRANK{i}',
                'species_reference': f'SPECIESREF{i}',
                'identified_by': f'IDENTIFIEDBY{i}',
                'sequence_run_site': f'RUNSITE{i}',
                'nuc': f'NUC{i}',
                'nuc_basecount': 321 + i,
                'sequence_upload_date': f'2024-03-0{i}',
                'bin_uri': f'BINURI{i}',
                'bin_created_date': f'2024-05-0{i}',
                'elev': 14 + i,
                'depth': 15 + i,
                'coord': [
                    50.7721 + i,
                    -3.90953 + i
                ],
                'coord_source': f'COORDSOURCE{i}',
                'coord_accuracy': f'COORDACCURACY{i}',
                'elev_accuracy': f'ELEVACCURACY{i}',
                'depth_accuracy': f'DEPTHACCURACY{i}',
                'region': f'REGION{i}',
                'sector': f'SECTOR{i}',
                'site': f'SITE{i}',
                'country_iso': f'COUNTRY{i}',
                'country/ocean': f'OCEAN{i}',
                'province/state': f'STATE{i}',
                'bold_recordset_code_arr': [
                    f'RECORDSET{i}'
                ],
                'collection_date_end': f'2024-06-0{i}'
            }
            for i in range(1, 3)
        ]
        resp = f'{json.dumps(objs[0])}\n{json.dumps(objs[1])}'
        expected = [
            objs[0],
            objs[1]
        ]

        responses.get(
            f'{FAKE_API_URL}/records',
            body=resp
        )

        observed = client.get_detail('sample', ['SAMPLE1', 'SAMPLE2'])
        assert observed == expected

    @responses.activate
    def test_get_detail_portal(self):
        """Default values, no token"""

        client = BoldApiClient(FAKE_API_URL, FAKE_API_URL, FAKE_API_KEY)
        query_response = {
            'query_id': 'FAKEQUERYID12345'
        }
        taxonomy_response = {
            'taxonomy': {
                'kingdom': {'Animalia': 937},
                'phylum': {'Arthropoda': 937},
                'class': {'Insecta': 937},
                'order': {'Diptera': 937},
                'family': {'Anthomyiidae': 936},
                'subfamily': {},
                'tribe': {},
                'genus': {'Botanophila': 913},
                'species': {'Botanophila fugax': 887, 'Botanophila sp. O111': 1},
                'subspecies': {}
            }
        }

        responses.get(
            f'{FAKE_API_URL}/query',
            json=query_response
        )
        responses.get(
            f'{FAKE_API_URL}/taxonomy/FAKEQUERYID12345',
            json=taxonomy_response
        )
        observed = list(client.get_detail('bin', ['BIN1234']))
        expected = [taxonomy_response['taxonomy'] | {'binid': 'BIN1234'}]
        assert observed == expected
