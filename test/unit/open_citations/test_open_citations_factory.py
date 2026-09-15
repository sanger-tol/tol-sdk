# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock

import responses

from tol.core import DataObject
from tol.open_citations import create_open_citations_datasource


FAKE_API_URL = 'http://fake.lan/api'


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


class TestCreateOpenCitationsDatasource:
    """larger-than unit tests on `create_open_citations_datasource`"""

    @responses.activate
    def test_get_by_id(self):
        """`create_open_citations_datasource().get_by_id()`"""

        open_citations_ds = create_open_citations_datasource(FAKE_API_URL)

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='meta',
            id_='10.1000/test',
        )
        mock_do_factory.return_value = mock_data_object
        open_citations_ds.data_object_factory = mock_do_factory

        responses.get(
            f'{FAKE_API_URL}/metadata/doi:10.1000/test',
            json=[{
                'id': 'doi:10.1000/test isbn:9780000000000 omid:br/1234',
                'title': 'A reference title',
                'author': 'Example, Alice; Writer, Bob',
                'pub_date': '2024-01-01',
                'venue': 'Journal of Examples',
                'type': 'journal article',
            }],
        )

        observed = list(open_citations_ds.get_by_id('meta', ['10.1000/test']))

        mock_do_factory.assert_called_once_with(
            'meta',
            id_='10.1000/test',
            attributes={
                'id': 'doi:10.1000/test isbn:9780000000000 omid:br/1234',
                'title': 'A reference title',
                'author': 'Example, Alice; Writer, Bob',
                'pub_date': '2024-01-01',
                'venue': 'Journal of Examples',
                'type': 'journal article',
            },
        )
        assert observed == [mock_data_object]

    @responses.activate
    def test_get_by_id_multiple(self):
        """Multiple ids, one of which is not found."""

        open_citations_ds = create_open_citations_datasource(FAKE_API_URL)

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='meta',
            id_='10.1000/test',
        )
        mock_do_factory.return_value = mock_data_object
        open_citations_ds.data_object_factory = mock_do_factory

        responses.get(
            f'{FAKE_API_URL}/metadata/doi:404__doi:10.1000/test',
            json=[{
                'id': 'doi:10.1000/test omid:br/1234',
                'title': 'A reference title',
                'author': 'Example, Alice; Writer, Bob',
                'pub_date': '2024-01-01',
                'venue': 'Journal of Examples',
                'type': 'journal article',
            }],
        )

        observed = list(open_citations_ds.get_by_id('meta', ['404', '10.1000/test']))

        mock_do_factory.assert_called_once_with(
            'meta',
            id_='10.1000/test',
            attributes={
                'id': 'doi:10.1000/test omid:br/1234',
                'title': 'A reference title',
                'author': 'Example, Alice; Writer, Bob',
                'pub_date': '2024-01-01',
                'venue': 'Journal of Examples',
                'type': 'journal article',
            },
        )
        assert observed == [None, mock_data_object]

    @responses.activate
    def test_get_by_id_uses_doi_when_response_identifier_order_varies(self):
        """Composite identifiers still parse to bare DOI ids."""

        open_citations_ds = create_open_citations_datasource(FAKE_API_URL)

        mock_do_factory = Mock()
        mock_data_object = _get_mock_data_object(
            type_='meta',
            id_='10.1000/test',
        )
        mock_do_factory.return_value = mock_data_object
        open_citations_ds.data_object_factory = mock_do_factory

        responses.get(
            f'{FAKE_API_URL}/metadata/doi:10.1000/test',
            json=[{
                'id': 'omid:br/1234 doi:10.1000/test',
                'title': 'A reference title',
                'author': 'Example, Alice; Writer, Bob',
                'pub_date': '2024-01-01',
                'venue': 'Journal of Examples',
                'type': 'journal article',
            }],
        )

        observed = list(open_citations_ds.get_by_id('meta', ['10.1000/test']))

        mock_do_factory.assert_called_once_with(
            'meta',
            id_='10.1000/test',
            attributes={
                'id': 'omid:br/1234 doi:10.1000/test',
                'title': 'A reference title',
                'author': 'Example, Alice; Writer, Bob',
                'pub_date': '2024-01-01',
                'venue': 'Journal of Examples',
                'type': 'journal article',
            },
        )
        assert observed == [mock_data_object]
