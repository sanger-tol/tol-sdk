# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock

import pytest

from tol.core import DataObject, DataSourceError, DataSourceFilter
from tol.open_citations import OpenCitationsDataSource


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: dict[str, Any] = {},
) -> DataObject:

    data_object = Mock()
    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes
    return data_object


class TestOpenCitationsDataSource:
    def test_get_by_id_found(self):
        """200 response."""

        mock_client = Mock()
        mock_client.get_detail.return_value = [{'id': 'doi:10.1000/test'}]

        mock_converter = Mock()

        ds = OpenCitationsDataSource(
            lambda: mock_client,
            lambda: mock_converter,
        )
        ds.data_object_factory = lambda: Mock()

        mock_data_object = _get_mock_data_object(
            type_='meta',
            id_='10.1000/test',
        )
        mock_converter.convert_list.return_value = ([mock_data_object], 1)

        observed = list(ds.get_by_id('meta', ['10.1000/test']))

        assert observed == [mock_data_object]
        mock_client.get_detail.assert_called_once_with('meta', ['10.1000/test'])
        mock_converter.convert_list.assert_called_once_with(
            'meta',
            [{'id': 'doi:10.1000/test'}],
        )

    def test_get_by_id_not_found(self):
        """404 response."""

        mock_client = Mock()
        mock_client.get_detail.return_value = []

        mock_converter = Mock()
        mock_converter.convert_list.return_value = ([], 0)

        ds = OpenCitationsDataSource(
            lambda: mock_client,
            lambda: mock_converter,
        )
        ds.data_object_factory = lambda: Mock()

        (observed,) = list(ds.get_by_id('meta', ['10.1000/test']))

        assert observed is None
        mock_client.get_detail.assert_called_once_with('meta', ['10.1000/test'])
        mock_converter.convert_list.assert_called_once_with('meta', [])

    def test_get_list_filters_by_id_in_list(self):
        mock_client = Mock()
        mock_client.get_detail.return_value = [{'id': 'pmid:12345678'}]
        mock_converter = Mock()
        mock_data_object = _get_mock_data_object(
            type_='meta',
            id_='10.1000/test',
        )
        mock_converter.convert_list.return_value = ([mock_data_object], 1)

        ds = OpenCitationsDataSource(
            lambda: mock_client,
            lambda: mock_converter,
        )

        observed = list(ds.get_list(
            'meta',
            object_filters=DataSourceFilter(and_={
                'reference_id': {'in_list': {'value': ['pmid:12345678']}},
            }),
        ))

        assert observed == [mock_data_object]
        mock_client.get_detail.assert_called_once_with('meta', ['pmid:12345678'])
        mock_converter.convert_list.assert_called_once_with(
            'meta',
            [{'id': 'pmid:12345678'}],
        )

    def test_get_list_page_filters_by_pmid(self):
        mock_client = Mock()
        mock_client.get_detail.return_value = [{'id': 'pmid:12345678'}]
        mock_converter = Mock()
        mock_data_object = _get_mock_data_object(
            type_='meta',
            id_='10.1000/test',
            attributes={'pmid': '12345678'},
        )
        mock_converter.convert_list.return_value = ([mock_data_object], 1)
        ds = OpenCitationsDataSource(
            lambda: mock_client,
            lambda: mock_converter,
        )
        object_filters = DataSourceFilter(and_={
            'reference_id': {
                'in_list': {
                    'value': ['pmid:12345678'],
                },
            },
        })

        objects, total = ds.get_list_page(
            'meta',
            1,
            object_filters=object_filters,
        )

        assert list(objects) == [mock_data_object]
        assert total == 1
        assert mock_data_object.id == '10.1000/test'
        assert mock_data_object.attributes['pmid'] == '12345678'
        mock_client.get_detail.assert_called_once_with(
            'meta',
            ['pmid:12345678'],
        )

    def test_get_list_page_paginates(self):
        mock_client = Mock()
        mock_client.get_detail.return_value = [
            {'id': 'pmid:11111111'},
            {'id': 'pmid:22222222'},
            {'id': 'pmid:33333333'},
        ]
        mock_converter = Mock()
        mock_data_objects = [
            _get_mock_data_object(
                type_='meta',
                id_=f'10.1000/test-{index}',
                attributes={'pmid': pmid},
            )
            for index, pmid in enumerate([
                '11111111',
                '22222222',
                '33333333',
            ])
        ]
        mock_converter.convert_list.return_value = (mock_data_objects, 3)
        ds = OpenCitationsDataSource(
            lambda: mock_client,
            lambda: mock_converter,
        )
        object_filters = DataSourceFilter(and_={
            'reference_id': {
                'in_list': {
                    'value': [
                        'pmid:11111111',
                        'pmid:22222222',
                        'pmid:33333333',
                    ],
                },
            },
        })

        objects, total = ds.get_list_page(
            'meta',
            2,
            page_size=1,
            object_filters=object_filters,
        )

        assert list(objects) == [mock_data_objects[1]]
        assert total == 3

    def test_get_list_page_empty(self):
        mock_client = Mock()
        mock_client.get_detail.return_value = []
        mock_converter = Mock()
        mock_converter.convert_list.return_value = ([], 0)
        ds = OpenCitationsDataSource(
            lambda: mock_client,
            lambda: mock_converter,
        )

        objects, total = ds.get_list_page(
            'meta',
            1,
            object_filters=DataSourceFilter(and_={
                'reference_id': {
                    'in_list': {
                        'value': ['pmid:99999999'],
                    },
                },
            }),
        )

        assert list(objects) == []
        assert total == 0

    @pytest.mark.parametrize('object_filters', [
        None,
        DataSourceFilter(),
        DataSourceFilter(and_={}),
        DataSourceFilter(and_={'reference_id': None}),
        DataSourceFilter(and_={'reference_id': {}}),
        DataSourceFilter(and_={'reference_id': {'in_list': None}}),
        DataSourceFilter(and_={'reference_id': {'in_list': {}}}),
    ])
    def test_get_list_requires_reference_ids(self, object_filters):
        ds = OpenCitationsDataSource(lambda: Mock(), lambda: Mock())

        with pytest.raises(DataSourceError) as error:
            list(ds.get_list('meta', object_filters=object_filters))

        assert error.value.title == (
            'Filter must contain reference_id in_list filter'
        )

    def test_get_list_page_requires_reference_ids(self):
        ds = OpenCitationsDataSource(lambda: Mock(), lambda: Mock())

        with pytest.raises(DataSourceError) as error:
            ds.get_list_page('meta', 1)

        assert error.value.title == (
            'Filter must contain reference_id in_list filter'
        )

    def test_bad_object_type(self):
        """A bad object type -> raise DataSourceError()."""

        ds = OpenCitationsDataSource(
            lambda: None,
            lambda: None,
        )

        with pytest.raises(DataSourceError):
            list(ds.get_by_id('bad_type', ['10.1000/test']))

        with pytest.raises(DataSourceError):
            ds.get_list_page(
                'bad_type',
                1,
                object_filters=DataSourceFilter(and_={
                    'reference_id': {
                        'in_list': {
                            'value': ['pmid:12345678'],
                        },
                    },
                }),
            )

    def test_supported_types(self):
        """OpenCitationsDataSource().supported_types."""

        ds = OpenCitationsDataSource(
            None,
            None,
        )

        observed = ds.supported_types

        assert observed == ['meta']
