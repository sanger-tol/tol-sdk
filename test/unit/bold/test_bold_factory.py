# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import json
from typing import Any, Optional
from unittest.mock import Mock

import responses

from tol.bold import create_bold_datasource
from tol.core import DataObject


FAKE_API_URL = 'http://fake.lan/api'
FAKE_API_KEY = 'key'


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: dict[str, Any] = {},
    to_one: dict[str, Any] = {}
) -> DataObject:

    data_object = Mock()

    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes
    data_object._to_one_objects = to_one

    return data_object


class TestCreateBoldDatasource:
    """larger-than unit tests on `create_bold_datasource`"""

    @responses.activate
    def test_get_by_id_sample(self):
        """`create_api_datasource().get_by_id()` + no token"""

        bold_ds = create_bold_datasource(FAKE_API_URL, FAKE_API_URL, FAKE_API_KEY)

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='sample',
            id_='SAMPLE1'
        )
        mock_do_factory.return_value = mock_data_object
        bold_ds.data_object_factory = mock_do_factory

        in_ = json.dumps({
            'sampleid': 'SAMPLE1',
            'bin_uri': 'BIN1'
        })

        responses.get(
            f'{FAKE_API_URL}/records',
            body=in_
        )

        observed = list(bold_ds.get_by_id('sample', ['SAMPLE1']))
        mock_do_factory.assert_called_once_with(
            'sample',
            id_='SAMPLE1',
            attributes={
                'bin_uri': 'BIN1'
            }
        )
        assert observed == [mock_data_object]

    @responses.activate
    def test_get_by_id_bin(self):
        """`create_api_datasource().get_by_id()` + no token"""

        bold_ds = create_bold_datasource(FAKE_API_URL, FAKE_API_URL, FAKE_API_KEY)

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='bin',
            id_='BIN1'
        )
        mock_do_factory.return_value = mock_data_object
        bold_ds.data_object_factory = mock_do_factory

        in_ = {
            'taxonomy': {
                'kingdom': {'kingdom1': 10},
                'phylum': {'phylum1': 10},
                'class': {'class1': 5},
                'order': {'order1': 2}
            }
        }

        responses.get(
            f'{FAKE_API_URL}/query',
            json={'query_id': 'FAKEQUERYID12345'}
        )
        responses.get(
            f'{FAKE_API_URL}/taxonomy/FAKEQUERYID12345',
            json=in_
        )

        observed = list(bold_ds.get_by_id('bin', ['BIN1']))
        mock_do_factory.assert_called_once_with(
            'bin',
            id_='BIN1',
            attributes={
                'kingdom': {'kingdom1': 10},
                'phylum': {'phylum1': 10},
                'class': {'class1': 5},
                'order': {'order1': 2}
            }
        )
        assert observed == [mock_data_object]

    @responses.activate
    def test_get_by_id_multiple(self):
        """
        Multiple statuses, one of which is not found + token
        """

        api_ds = create_bold_datasource(
            FAKE_API_URL,
            FAKE_API_URL,
            FAKE_API_KEY
        )

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='sample',
            id_='SAMPLE1'
        )
        mock_do_factory.return_value = mock_data_object
        api_ds.data_object_factory = mock_do_factory

        obj1 = {'sampleid': 'SAMPLE1', 'bin_uri': 'BIN1'}
        in_ = json.dumps(obj1)

        responses.get(
            f'{FAKE_API_URL}/records',
            body=in_
        )

        observed = list(
            api_ds.get_by_id('sample', ['404', 'SAMPLE1'])
        )
        mock_do_factory.assert_called_once_with(
            'sample',
            id_='SAMPLE1',
            attributes={
                'bin_uri': 'BIN1'
            }
        )
        assert observed == [None, mock_data_object]
