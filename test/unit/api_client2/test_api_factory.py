# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock, PropertyMock

import responses
from responses.matchers import (
    header_matcher,
    json_params_matcher
)

from tol.api_client2 import create_api_datasource
from tol.core.operator import ReturnMode


FAKE_API_URL = 'http://fake.lan/api/v42'


class TestCreateApiDatasource:
    """larger-than unit tests on `create_api_datasource`"""

    @responses.activate
    def test_get_by_id(self):
        """`create_api_datasource().get_by_id()` + no token"""

        api_ds = create_api_datasource(FAKE_API_URL)

        mock_do_factory = Mock()
        mock_data_object = Mock()
        mock_do_factory.return_value = mock_data_object
        api_ds.data_object_factory = mock_do_factory

        in_ = {
            'data': {
                'type': 'test',
                'id': 'hype',
                'attributes': {
                    'yes': False
                }
            }
        }

        responses.get(
            f'{FAKE_API_URL}/data/test/hype',
            json=in_
        )
        self.__responses_preflight_check('test', ['detailGet'])

        observed = list(api_ds.get_by_id('test', ['hype']))

        mock_do_factory.assert_called_once_with(
            'test',
            id_='hype',
            attributes={'yes': False},
            to_one={}
        )
        assert observed == [mock_data_object]

    @responses.activate
    def test_get_by_id_multiple(self):
        """
        Multiple statuses, one of which is not found + token
        """

        api_ds = create_api_datasource(
            FAKE_API_URL,
            token='lol'
        )

        mock_do_factory = Mock()
        mock_data_object = Mock()
        mock_do_factory.return_value = mock_data_object
        api_ds.data_object_factory = mock_do_factory

        in_ = {
            'data': {
                'type': 'test',
                'id': '200',
                'attributes': {
                    'yes': False
                }
            }
        }

        responses.get(
            f'{FAKE_API_URL}/data/test/200',
            json=in_,
            match=[
                header_matcher({'token': 'lol'}),
            ]
        )
        responses.get(
            f'{FAKE_API_URL}/data/test/404',
            status=404,
            match=[
                header_matcher({'token': 'lol'}),
            ]
        )
        self.__responses_preflight_check('test', ['detailGet'])

        observed = list(
            api_ds.get_by_id('test', ['404', '200'])
        )

        mock_do_factory.assert_called_once_with(
            'test',
            id_='200',
            attributes={'yes': False},
            to_one={}
        )
        assert observed == [None, mock_data_object]

    @responses.activate
    def test_delete(self):
        """`create_api_datasource().delete()`"""

        api_ds = create_api_datasource(
            FAKE_API_URL,
            token='funds'
        )
        expected_url = f'{FAKE_API_URL}/data/test/2'

        responses.delete(
            expected_url,
            match=[
                header_matcher({'token': 'funds'}),
            ]
        )
        self.__responses_preflight_check('test', ['delete'])

        api_ds.delete('test', ['2'])

    @responses.activate
    def test_upsert(self):
        """`create_api_datasource().upsert()`"""

        api_ds = create_api_datasource(
            FAKE_API_URL,
            token='cool'
        )

        def __mock_object(
            type_: str,
            id_: Optional[str] = None,
            data: Optional[dict[str, Any]] = {}
        ) -> Mock:

            mock_object = Mock()
            type(mock_object).type = PropertyMock(return_value=type_)
            type(mock_object).id = PropertyMock(return_value=id_)
            type(mock_object).attributes = PropertyMock(
                return_value=data
            )

            return mock_object

        in_ = [
            __mock_object('a_test_lol', str(i + 1), {'test_int': i})
            for i in range(4)
        ]
        expected_list = [
            {
                'type': 'a_test_lol',
                'id': str(i + 1),
                'attributes': {
                    'test_int': i
                }
            }
            for i in range(4)
        ]
        expected_json = {'data': expected_list}

        expected_url = f'{FAKE_API_URL}/data/test2:upsert'
        responses.post(
            expected_url,
            match=[
                header_matcher({'token': 'cool'}),
                json_params_matcher(
                    expected_json,
                    strict_match=True
                )
            ],
            json={
                'data': []
            }
        )
        self.__responses_preflight_check('test2', ['upsert'])

        api_ds.upsert('test2', in_)

    def __responses_preflight_check(
        self,
        object_type: str,
        operation_names: list[str]
    ):
        """adds pre-flight checks to `responses`"""

        responses.get(
            f'{FAKE_API_URL}/data/_config/operations',
            json={
                object_type: {'noauth': operation_names}
            }
        )
        responses.get(
            f'{FAKE_API_URL}/data/_config/attribute_types',
            json={object_type: {}}
        )
        responses.get(
            f'{FAKE_API_URL}/data/_config/return_mode',
            json={object_type: ReturnMode.NONE}
        )
