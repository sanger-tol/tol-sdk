# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core.data_object import DataObject

from .mock import api_ds, mock_upsert


class TestApiDataSource:
    @mock_upsert()
    def test_no_upsert_no_call(self, upsert_mock):
        with api_ds.session():
            pass
        assert upsert_mock.call_count == 0

    @mock_upsert()
    def test_one_upsert_one_call(self, upsert_mock):
        with api_ds.session() as sess:
            objects = [
                DataObject(
                    'test',
                    {
                        'id': str(i)
                    }
                )
                for i in range(100)
            ]
            sess.upsert(objects)
        assert upsert_mock.call_count == 1

    @mock_upsert()
    def test_many_upsert_types_one_call(self, upsert_mock):
        with api_ds.session() as sess:
            objects = [
                DataObject(
                    f'test_{i}',
                    {
                        'field1': 'great fun :)'
                    }
                )
                for i in range(100)
            ]
            sess.upsert(objects)
        assert upsert_mock.call_count == 1

    @mock_upsert()
    def test_to_one_relationship(self, upsert_mock):
        species = DataObject(
            'species',
            {
                'id': '9606',
                'name': 'Homo sapiens'
            }
        )
        specimen = DataObject(
            'specimens',
            {
                'id': 'mHomSap9534'
            }
        )
        specimen.species = species
        with api_ds.session() as sess:
            sess.upsert([specimen])
        assert upsert_mock.call_count == 1
        expected = [
            {
                'type': 'species',
                '_uuid': species._request_internal_uuid,
                'id': '9606',
                'attributes': {
                    'name': 'Homo sapiens'
                }
            },
            {
                'type': 'specimens',
                '_uuid': specimen._request_internal_uuid,
                'id': 'mHomSap9534'
            }
        ]
        observed = upsert_mock.calls[0].request.json()
        assert expected == observed

    @mock_upsert()
    def test_to_many_relationship(self, upsert_mock):
        pass

    @mock_upsert()
    def test_attributes_and_relationships(self, upsert_mock):
        pass
