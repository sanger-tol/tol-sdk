# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import responses

from tol.ena.client import EnaApiClient

FAKE_ENA_URL = 'https://test.lan/api'
FAKE_ENA_USER = 'user'
FAKE_ENA_PASS = 'pass'
FAKE_ENA_CONTACT = 'contact'
FAKE_ENA_EMAIL = 'email'


class TestEnaClient:
    """The `EnaApiClient` and it's methods."""

    @responses.activate
    def test_get_detail(self):
        """Default values."""

        client = EnaApiClient(
            ena_url=FAKE_ENA_URL,
            ena_user=FAKE_ENA_USER,
            ena_password=FAKE_ENA_PASS,
            ena_contact_name=FAKE_ENA_CONTACT,
            ena_contact_email=FAKE_ENA_EMAIL
        )

        resp = [
            {
                'tax_id': '9662',
                'scientific_name': 'Meles meles',
                'lineage': 'Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; Euteleostomi; Mammalia; Eutheria; Laurasiatheria; Carnivora; Caniformia; Musteloidea; Mustelidae; Melinae; Meles; ', # noqa
                'genetic_code': '1',
                'merged_tax_id': '',
                'description': 'Meles meles',
                'accession': '9662',
                'synonym': 'Ursus meles Linnaeus;1758:authority;Ursus meles:synonym;Eurasian badger:genbank common name;Meles meles:scientific name', # noqa
                'tax_lineage': '1;131567;2759;33154;33208;6072;33213;33511;7711;89593;7742;7776;117570;117571;8287;1338369;32523;32524;40674;32525;9347;1437010;314145;33554;379584;3072906;9655;1008252;9661;9662', # noqa
                'rank': 'species',
                'tag': '',
                'common_name': '',
                'tax_division': 'MAM',
                'genbank_common_name': 'Eurasian badger',
                'status': 'public'
            },
            {
                'tax_id': '126867',
                'scientific_name': 'Phalacrocorax aristotelis',
                'lineage': 'Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; Euteleostomi; Archelosauria; Archosauria; Dinosauria; Saurischia; Theropoda; Coelurosauria; Aves; Neognathae; Neoaves; Aequornithes; Suliformes; Phalacrocoracidae; Phalacrocorax; ', # noqa
                'genetic_code': '1',
                'merged_tax_id': '',
                'description': 'Phalacrocorax aristotelis',
                'accession': '126867',
                'synonym': 'Gulosus aristotelis (Linnaeus;1761):authority;Phalacrocorax aristotelis (Linnaeus;1761):authority;Pelecanus aristotelis Linnaeus;1761:authority;European shag:common name;Leucocarbo aristotelis:synonym;Gulosus aristotelis:synonym;Pelecanus aristotelis:synonym;Phalacrocorax aristotelis:scientific name', # noqa
                'tax_lineage': '1;131567;2759;33154;33208;6072;33213;33511;7711;89593;7742;7776;117570;117571;8287;1338369;32523;32524;8457;32561;1329799;8492;436486;436489;436491;436492;8782;8825;3078114;3073812;3073854;9206;9207;126867', # noqa
                'rank': 'species',
                'tag': 'env_tax:terrestrial;env_tax:marine;xref:WoRMS',
                'common_name': 'European shag',
                'tax_division': 'VRT',
                'genbank_common_name': '',
                'status': 'public'
            }
        ]

        expected = [
            {
                'tax_id': '9662',
                'scientific_name': 'Meles meles',
                'lineage': 'Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; Euteleostomi; Mammalia; Eutheria; Laurasiatheria; Carnivora; Caniformia; Musteloidea; Mustelidae; Melinae; Meles; ', # noqa
                'genetic_code': '1',
                'merged_tax_id': '',
                'description': 'Meles meles',
                'accession': '9662',
                'synonym': 'Ursus meles Linnaeus;1758:authority;Ursus meles:synonym;Eurasian badger:genbank common name;Meles meles:scientific name', # noqa
                'tax_lineage': '1;131567;2759;33154;33208;6072;33213;33511;7711;89593;7742;7776;117570;117571;8287;1338369;32523;32524;40674;32525;9347;1437010;314145;33554;379584;3072906;9655;1008252;9661;9662', # noqa
                'rank': 'species',
                'tag': '',
                'common_name': '',
                'tax_division': 'MAM',
                'genbank_common_name': 'Eurasian badger',
                'status': 'public'
            },
            {
                'tax_id': '126867',
                'scientific_name': 'Phalacrocorax aristotelis',
                'lineage': 'Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; Euteleostomi; Archelosauria; Archosauria; Dinosauria; Saurischia; Theropoda; Coelurosauria; Aves; Neognathae; Neoaves; Aequornithes; Suliformes; Phalacrocoracidae; Phalacrocorax; ', # noqa
                'genetic_code': '1',
                'merged_tax_id': '',
                'description': 'Phalacrocorax aristotelis',
                'accession': '126867',
                'synonym': 'Gulosus aristotelis (Linnaeus;1761):authority;Phalacrocorax aristotelis (Linnaeus;1761):authority;Pelecanus aristotelis Linnaeus;1761:authority;European shag:common name;Leucocarbo aristotelis:synonym;Gulosus aristotelis:synonym;Pelecanus aristotelis:synonym;Phalacrocorax aristotelis:scientific name', # noqa
                'tax_lineage': '1;131567;2759;33154;33208;6072;33213;33511;7711;89593;7742;7776;117570;117571;8287;1338369;32523;32524;8457;32561;1329799;8492;436486;436489;436491;436492;8782;8825;3078114;3073812;3073854;9206;9207;126867', # noqa
                'rank': 'species',
                'tag': 'env_tax:terrestrial;env_tax:marine;xref:WoRMS',
                'common_name': 'European shag',
                'tax_division': 'VRT',
                'genbank_common_name': '',
                'status': 'public'
            }
        ]

        responses.get(
            f'{FAKE_ENA_URL}/ena/portal/api/search',
            json=resp
        )

        observed = client.get_detail('taxon', ['9662', '126867'])
        assert observed == (expected)

    @responses.activate
    def test_get_fields(self):
        """Default values."""

        client = EnaApiClient(
            ena_url=FAKE_ENA_URL,
            ena_user=FAKE_ENA_USER,
            ena_password=FAKE_ENA_PASS,
            ena_contact_name=FAKE_ENA_CONTACT,
            ena_contact_email=FAKE_ENA_EMAIL
        )

        objs = [
            {
                'columnId': 'common_name',
                'description': 'Everyday name for an organism',
                'type': 'text'
            },
            {
                'columnId': 'description',
                'description': 'brief sequence description',
                'type': 'text'
            },
            {
                'columnId': 'genbank_common_name',
                'description': 'Everyday name for an organism in GenBank',
                'type': 'text'
            },
            {
                'columnId': 'genetic_code',
                'description': 'Set of rules that determine sequence translation',
                'type': 'number'
            },
            {
                'columnId': 'lineage',
                'description': 'names representing hierarchical classification of an organism ',
                'type': 'text'
            },
            {
                'columnId': 'merged_tax_id',
                'description': 'Old tax ids merged to this tax id',
                'type': 'number'
            },
            {
                'columnId': 'rank',
                'description': 'Relative level of a group of organisms in an ancestral hierarchy.',
                'type': 'text'
            },
            {
                'columnId': 'scientific_name',
                'description': 'scientific name of an organism',
                'type': 'text'
            },
            {
                'columnId': 'status',
                'description': 'Status',
                'type': 'number'
            },
            {
                'columnId': 'synonym',
                'description': 'Synonyms for taxon',
                'type': 'text'
            },
            {
                'columnId': 'tag',
                'description': 'Classification Tags',
                'type': 'controlled value'
            },
            {
                'columnId': 'tax_division',
                'description': 'taxonomic division',
                'type': 'controlled value'
            },
            {
                'columnId': 'tax_id',
                'description': 'NCBI taxonomic classification',
                'type': 'taxonomy'
            },
            {
                'columnId': 'tax_lineage',
                'description': 'Complete taxonomic lineage for an organism',
                'type': 'text'
            }
        ]

        resp = objs

        expected_fields = {
            'common_name': 'str',
            'description': 'str',
            'genbank_common_name': 'str',
            'genetic_code': 'float',
            'lineage': 'str',
            'merged_tax_id': 'float',
            'rank': 'str',
            'scientific_name': 'str',
            'status': 'float',
            'synonym': 'str',
            'tag': 'str',
            'tax_division': 'str',
            'tax_id': 'str',
            'tax_lineage': 'str'
        }

        responses.get(
            f'{FAKE_ENA_URL}/ena/portal/api/returnFields?result=' + 'taxon&format=json',
            json=resp
        )

        fields = client.get_fields('taxon')
        assert fields == expected_fields
