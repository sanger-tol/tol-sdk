# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock

import responses

from tol.copo import create_copo_datasource


FAKE_API_URL = 'http://fake.lan/api'


class TestCreateCopoDatasource:
    """larger-than unit tests on `create_api_datasource`"""

    @responses.activate
    def test_get_by_id(self):
        """`create_copo_datasource().get_by_id()` + no token"""

        copo_ds = create_copo_datasource(FAKE_API_URL)

        mock_do_factory = Mock()
        mock_data_object = Mock()
        mock_do_factory.return_value = mock_data_object
        copo_ds.data_object_factory = mock_do_factory

        in_ = {
            'data': [
                {
                    'copo_id': 'hype',
                    'public_name': 'Yo'
                }
            ]
        }

        responses.get(
            f'{FAKE_API_URL}/sample/copo_id/hype',
            json=in_
        )

        observed = list(copo_ds.get_by_id('sample', ['hype']))

        mock_do_factory.assert_called_once_with(
            'sample',
            id_='hype',
            attributes={'public_name': 'Yo'}
        )
        assert observed == [mock_data_object]

    @responses.activate
    def test_get_by_id_multiple(self):
        """
        Multiple statuses, one of which is not found + token
        """

        copo_ds = create_copo_datasource(
            FAKE_API_URL
        )

        mock_do_factory = Mock()
        mock_data_object = Mock()
        mock_do_factory.return_value = mock_data_object
        copo_ds.data_object_factory = mock_do_factory

        in_ = {
            'data': [
                {
                    'copo_id': '200',
                    'public_name': 'Yo'
                }
            ]
        }

        responses.get(
            f'{FAKE_API_URL}/sample/copo_id/200',
            json=in_
        )
        responses.get(
            f'{FAKE_API_URL}/sample/copo_id/404',
            status=404
        )

        observed = list(
            copo_ds.get_by_id('sample', ['404', '200'])
        )

        mock_do_factory.assert_called_once_with(
            'sample',
            id_='200',
            attributes={'public_name': 'Yo'}
        )
        assert observed == [None, mock_data_object]
