# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

from tol.api_client.api_data_object import ApiResponseDataObject


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
        ApiResponseDataObject(
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
        mock_b = ApiResponseDataObject(
            ds,
            {
                'type': 'B',
                'id': '1234'
            }
        )
        get_mock.return_value = []
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
        api_object = ApiResponseDataObject(
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

    def test_several_different_to_one_relationships(self):
        """
        N access to N different to-one relationships -> N
        method calls, one for each
        """

    def __mock_datasource(self, mock_get_by_id: MagicMock) -> object:
        return type(
            '',
            (object,),
            {
                'get_by_id': mock_get_by_id
            }
        )
