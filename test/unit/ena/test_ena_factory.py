# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock

import responses

from tol.core import DataObject
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
