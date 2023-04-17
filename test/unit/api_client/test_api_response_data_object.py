# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

from tol.api_client.api_data_object import (
    ApiResponseDataObject,
    new_api_response_data_object
)


class TestApiResponseDataObject:
    def test_no_relationship_access_no_get(self):
        """
        Not accessing any relationships -> no get methods
        are called on the provided datasource
        """
        get_mock = MagicMock()
        ds = self.__mock_datasource(get_mock)
        loaded = {
            'type': 'test',
            'id': '1234'
        }
        new_api_response_data_object(
            ds,
            loaded,
            data={
                'test': 'hype'
            },
        )
        get_mock.assert_not_called()

    def test_to_one_relationship(self):
        """
        Accessing one to-one relationship -> one get method
        call
        """
        get_mock = MagicMock()
        ds = self.__mock_datasource(get_mock)
        mock_b = new_api_response_data_object(
            ds,
            {
                'type': 'B',
                'id': '1234'
            }
        )
        get_mock.return_value = [mock_b]
        loaded = {
            'type': 'A',
            'id': '2913408',
            'relationships': {
                'test_b': {
                    'data': {
                        'type': 'B',
                        'id': '1234'
                    }
                }
            }
        }
        api_object = new_api_response_data_object(
            ds,
            loaded
        )
        test_b = api_object.test_b
        get_mock.assert_called_once_with(
            'B',
            ['1234']
        )
        assert mock_b == test_b


    def test_repeated_to_one_relationship(self):
        """
        Repeated access of to-one relationship -> just
        one get method call (should be cached)
        """
        get_mock = MagicMock()
        ds = self.__mock_datasource(get_mock)
        loaded = {
            'type': 'A',
            'id': '2913408',
            'relationships': {
                'test_b': {
                    'data': {
                        'type': 'B',
                        'id': '1234'
                    }
                }
            }
        }
        api_object = new_api_response_data_object(
            ds,
            loaded
        )
        for _ in range(55):
            _ = api_object.test_b
        get_mock.assert_called_once_with(
            'B',
            ['1234']
        )

    def test_several_different_to_one_relationships(self):
        """
        N access to N different to-one relationships -> N
        method calls, one for each
        """
        get_mock = MagicMock()
        ds = self.__mock_datasource(get_mock)
        relationships_loaded = {
            f'test_{i}': {
                'data': {
                    'type': str(i),
                    'id': '1234'
                }
            }
            for i in range(44)
        }
        loaded = {
            'type': 'A',
            'id': '2913408',
            'relationships': relationships_loaded
        }
        api_object = new_api_response_data_object(
            ds,
            loaded
        )
        for i in range(44):
            getattr(api_object, f'test_{i}')
        assert get_mock.call_count == 44
        for i in range(44):
            get_mock.assert_any_call(
                str(i),
                ['1234']
            )

    def __mock_datasource(self, mock_get_by_id: MagicMock) -> object:
        return type(
            '',
            (object,),
            {
                'get_by_id': mock_get_by_id
            }
        )
