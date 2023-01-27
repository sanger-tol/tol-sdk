# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import TestCase

import responses

from tol.api_utils import (
    ApiDataSource,
    ApiObject
)
from tol.core import DataSourceError


class TestApiDataSource(TestCase):
    MOCK_URL = 'http://mock.url'
    MOCK_KEY = 'mock-key'

    @responses.activate
    def test_get_by_id(self):
        mock_response = {'data': {'type': 'species',
                                  'id': 1234,
                                  'attributes': {'taxonomyId': '6344',
                                                 'scientificName': 'Arenicola marina',
                                                 'commonName': 'lugworm',
                                                 'family': 'Arenicolidae',
                                                 'genus': 'Arenicola',
                                                 'order': 'None',
                                                 'phylum': None}}}
        responses.add(responses.GET, self.MOCK_URL + '/species/1234',
                      json=mock_response, status=200)
        ads = ApiDataSource({'url': self.MOCK_URL, 'key': self.MOCK_KEY})
        species = ads.get_by_id('species', 1234)
        self.assertEqual(species.taxonomy_id, '6344')
        self.assertEqual(species.scientific_name, 'Arenicola marina')
        self.assertEqual(species.common_name, 'lugworm')
        self.assertEqual(species.genus, 'Arenicola')
        self.assertEqual(species.order, 'None')
        self.assertIsNone(species.phylum)

    @responses.activate
    def test_get_list(self):
        mock_response = {'meta': {'total': 2},
                         'data': [{'type': 'species',
                                   'id': 1234,
                                   'attributes': {'taxonomyId': '6344',
                                                  'scientificName': 'Arenicola marina',
                                                  'commonName': 'lugworm',
                                                  'family': 'Arenicolidae',
                                                  'genus': 'Arenicola',
                                                  'order': 'None',
                                                  'phylum': None}}]}
        responses.add(responses.GET, self.MOCK_URL + '/species?page=1&page_size=1',
                      json=mock_response, status=200)
        mock_response = {'meta': {'total': 2},
                         'data': [{'type': 'species',
                                   'id': 5678,
                                   'attributes': {'taxonomyId': '9606',
                                                  'scientificName': 'Homo sapiens',
                                                  'commonName': 'human',
                                                  'family': 'Mammalia',
                                                  'genus': 'Homo',
                                                  'order': 'None',
                                                  'phylum': None}}]}
        responses.add(responses.GET, self.MOCK_URL + '/species?page=2&page_size=1',
                      json=mock_response, status=200)
        ads = ApiDataSource({'url': self.MOCK_URL, 'key': self.MOCK_KEY})
        species = list(ads.get_list('species', page_size=1))
        self.assertEqual(len(species), 2)
        s = species[0]
        self.assertEqual(s.taxonomy_id, '6344')
        self.assertEqual(s.scientific_name, 'Arenicola marina')
        self.assertEqual(s.common_name, 'lugworm')
        self.assertEqual(s.genus, 'Arenicola')
        self.assertEqual(s.order, 'None')
        self.assertIsNone(s.phylum)
        s = species[1]
        self.assertEqual(s.taxonomy_id, '9606')
        self.assertEqual(s.scientific_name, 'Homo sapiens')
        self.assertEqual(s.common_name, 'human')
        self.assertEqual(s.genus, 'Homo')
        self.assertEqual(s.order, 'None')
        self.assertIsNone(s.phylum)

    @responses.activate
    def test_delete(self):
        responses.add(responses.DELETE, self.MOCK_URL + '/species/1111',
                      status=404)
        responses.add(responses.DELETE, self.MOCK_URL + '/species/1234',
                      status=204)
        ads = ApiDataSource({'url': self.MOCK_URL, 'key': self.MOCK_KEY})
        with self.assertRaises(DataSourceError):
            ads.delete_by_id('species', 1111)
        ads.delete_by_id('species', 1234)

    @responses.activate
    def test_create(self):
        mock_response = {'data': {'type': 'species',
                                  'id': 1234,
                                  'attributes': {'taxonomyId': 6344,
                                                 'scientificName': 'Arenicola marina',
                                                 'commonName': 'lugworm',
                                                 'family': 'Arenicolidae',
                                                 'genus': 'Arenicola',
                                                 'order': 'None',
                                                 'phylum': None}}}
        responses.add(responses.POST, self.MOCK_URL + '/species',
                      json=mock_response, status=200)
        ads = ApiDataSource({'url': self.MOCK_URL, 'key': self.MOCK_KEY})
        s = ApiObject('species', None, mock_response['data']['attributes'])
        ads.create(s)
        self.assertEqual(s.type, 'species')
        self.assertEqual(s.id, 1234)
        self.assertEqual(s.taxonomy_id, 6344)
        self.assertEqual(s.scientific_name, 'Arenicola marina')
        self.assertEqual(s.common_name, 'lugworm')
        self.assertEqual(s.genus, 'Arenicola')
        self.assertEqual(s.order, 'None')
        self.assertIsNone(s.phylum)

    @responses.activate
    def test_update(self):
        mock_response = {'data': {'type': 'species',
                                  'id': 1234,
                                  'attributes': {'taxonomyId': 6344,
                                                 'scientificName': 'Arenicola marina',
                                                 'commonName': 'lugworm',
                                                 'family': 'Arenicolidae',
                                                 'genus': 'Arenicola',
                                                 'order': 'None',
                                                 'phylum': None}}}
        responses.add(responses.PATCH, self.MOCK_URL + '/species/1234',
                      json=mock_response, status=200)
        ads = ApiDataSource({'url': self.MOCK_URL, 'key': self.MOCK_KEY})
        s = ApiObject.create(mock_response['data'])  # Create the species
        species = ads.update(s)
        self.assertEqual(species.taxonomy_id, 6344)
        self.assertEqual(species.scientific_name, 'Arenicola marina')
        self.assertEqual(species.common_name, 'lugworm')
        self.assertEqual(species.genus, 'Arenicola')
        self.assertEqual(species.order, 'None')
        self.assertIsNone(species.phylum)
