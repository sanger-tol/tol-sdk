# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Optional
from unittest.mock import Mock, create_autospec

from tol.core import DataObject, DataSource
from tol.core.data_source_dict import DataSourceDict
from tol.open_citations.converter import OpenCitationsApiConverter
from tol.open_citations.parser import DefaultParser


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


def _get_mock_data_source(
    attribute_types: dict[str, dict[str, Any]] = {},
) -> DataSource:
    mock_ds = create_autospec(DataSource, spec_set=True)
    mock_ds.attribute_types = attribute_types
    mock_ds.supported_types = list(attribute_types.keys())
    mock_ds.data_object_factory = _get_mock_data_object
    return mock_ds


def _get_mock_ds_dict(
    attribute_types: dict[str, dict[str, Any]] = {},
) -> dict[str, DataSource]:
    return DataSourceDict(
        _get_mock_data_source(attribute_types=attribute_types)
    )


class TestOpenCitationsApiConverter:
    """Tests `OpenCitationsApiConverter`.convert()."""

    def test_convert(self):
        """Test convert()."""

        parser = DefaultParser(_get_mock_ds_dict({'meta': {
            'id': 'str',
            'title': 'str',
            'author': 'str',
            'pub_date': 'str',
            'venue': 'str',
            'type': 'str',
        }}))
        converter = OpenCitationsApiConverter(parser)

        in_ = {
            'id': 'doi:10.1000/test omid:br/1234',
            'title': 'A reference title',
            'author': 'Example, Alice',
            'pub_date': '2024-01-01',
            'venue': 'Journal of Examples',
            'type': 'journal article',
            'ignored_field': 'ignored',
        }

        observed = converter.convert('meta', in_)

        assert observed.type == 'meta'
        assert observed.id == '10.1000/test'
        assert observed.attributes == {
            'id': 'doi:10.1000/test omid:br/1234',
            'title': 'A reference title',
            'author': 'Example, Alice',
            'pub_date': '2024-01-01',
            'venue': 'Journal of Examples',
            'type': 'journal article',
        }

    def test_convert_list(self):
        """Test convert_list()."""

        parser = DefaultParser(_get_mock_ds_dict({'meta': {
            'id': 'str',
            'title': 'str',
        }}))
        converter = OpenCitationsApiConverter(parser)

        in_ = [
            {
                'id': 'doi:10.1000/test-1 omid:br/111',
                'title': 'First reference',
            },
            {
                'id': 'omid:br/222 doi:10.1000/test-2',
                'title': 'Second reference',
            },
        ]

        observed, count = converter.convert_list('meta', in_)

        assert count == 2
        first = observed[0]
        assert first.type == 'meta'
        assert first.id == '10.1000/test-1'
        second = observed[1]
        assert second.type == 'meta'
        assert second.id == '10.1000/test-2'
