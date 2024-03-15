# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock

import responses

from tol.labwhere import create_labwhere_datasource


FAKE_API_URL = 'http://fake.lan/api'


class TestCreateApiDatasource:
    """larger-than unit tests on `create_api_datasource`"""

    @responses.activate
    def test_get_by_id(self):
        """`create_api_datasource().get_by_id()` + no token"""

        labwhere_ds = create_labwhere_datasource(FAKE_API_URL)

        mock_do_factory = Mock()
        mock_data_object = Mock()
        mock_do_factory.return_value = mock_data_object
        labwhere_ds.data_object_factory = mock_do_factory

        in_ = {
            'location_type_id': 'test',
            'barcode': 'hype',
            'name': 'Yo'
        }

        responses.get(
            f'{FAKE_API_URL}/locations/hype',
            json=in_
        )

        observed = list(labwhere_ds.get_by_id('location', ['hype']))

        mock_do_factory.assert_called_once_with(
            'location',
            id_='hype',
            attributes={'name': 'Yo', 'location_type_id': 'test'}
        )
        assert observed == [mock_data_object]

    @responses.activate
    def test_get_by_id_multiple(self):
        """
        Multiple statuses, one of which is not found + token
        """

        api_ds = create_labwhere_datasource(
            FAKE_API_URL
        )

        mock_do_factory = Mock()
        mock_data_object = Mock()
        mock_do_factory.return_value = mock_data_object
        api_ds.data_object_factory = mock_do_factory

        in_ = {
            'location_type_id': 'test',
            'barcode': '200',
            'name': 'Yo'
        }

        responses.get(
            f'{FAKE_API_URL}/locations/200',
            json=in_
        )
        responses.get(
            f'{FAKE_API_URL}/locations/404',
            status=404
        )

        observed = list(
            api_ds.get_by_id('location', ['404', '200'])
        )

        mock_do_factory.assert_called_once_with(
            'location',
            id_='200',
            attributes={'name': 'Yo', 'location_type_id': 'test'}
        )
        assert observed == [None, mock_data_object]
