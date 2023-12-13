# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from typing import Any, Optional
from unittest.mock import Mock, create_autospec

from tol.api_client2.converter import (
    DataObjectConverter,
    JsonApiConverter
)
from tol.core import DataObject, DataSource


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


def _get_mock_data_source(
    attribute_types: dict[str, dict[str, Any]] = {}
) -> DataSource:

    mock_ds = create_autospec(DataSource, spec_set=True)

    mock_ds.attribute_types = attribute_types
    mock_ds.supported_types = list(attribute_types.keys())
    mock_ds.data_object_factory = _get_mock_data_object

    return mock_ds


class TestJsonApiConverter:
    """Tests `JsonApiConverter().convert()`"""

    def test_no_relationships(self):
        """A resource without relationships"""

        in_ = {
            'data': [
                {
                    'type': 'A',
                    'id': str(i),
                    'attributes': {'int_I': i}
                }
                for i in range(4)
            ]
        }

        converter = JsonApiConverter(_get_mock_data_source())
        (out_, _) = converter.convert_list(in_)

        assert len(out_) == 4
        for i in range(4):
            out_i = out_[i]
            assert out_i.type == 'A'
            assert out_i.id == str(i)
            assert out_i.attributes == {'int_I': i}

    def test_no_optional(self):
        """Optional fields not specified"""

        in_ = {
            'data_lol': {
                'type': 'hype'
            }
        }
        converter = JsonApiConverter(
            _get_mock_data_source(),
            data_key='data_lol'
        )
        out_ = converter.convert(in_)

        assert out_.type == 'hype'
        assert out_.id is None
        assert not out_.attributes

    def test_convert_relationship_config(self):
        """
        `JsonApiConverter().convert_relationship_config()`
        with a complex input.
        """

        in_ = {
            'a': {
                'one': {
                    'bee movie': 'b'
                },
                'many': {
                    'high seas': 'c',
                    'overboard': 'planks'
                }
            },
            'planks': {
                'many': {
                    'ahoy': 'me_mateys'
                }
            }
        }

        converter = JsonApiConverter(None)

        out_ = converter.convert_relationship_config(in_)

        assert list(out_.keys()) == ['a', 'planks']
        assert out_['a'].to_one == {'bee movie': 'b'}
        assert out_['a'].to_many == {
            'high seas': 'c',
            'overboard': 'planks'
        }
        assert not out_['planks'].to_one
        assert out_['planks'].to_many == {'ahoy': 'me_mateys'}

    def test_datetime(self):
        """
        All `datetime` attributes, as defined in
        `ApiDataSource().attribute_types`, are parsed.
        """

        now = str(datetime.now())

        in_ = {
            'data': {
                'type': 'test',
                'id': 'lol',
                'attributes': {
                    'a': now,
                    'b': now,
                    'c': now,
                    'd': now
                }
            }
        }

        attribute_types = {
            'test': {
                'a': 'datetime',
                'b': 'Date',
                'c': 'tImE',
                # below should not parse as `datetime`
                'd': 'str'
            }
        }

        mock_ds = _get_mock_data_source(
            attribute_types=attribute_types
        )

        converter = JsonApiConverter(mock_ds)

        observed = converter.convert(in_)

        for c in 'abc':
            assert isinstance(
                observed.attributes[c],
                datetime
            )
        assert isinstance(observed.attributes['d'], str)

    def test_relationships(self):
        """
        A resource with relationships. Tests:
        - relationships
        - different `data_key` kwarg
        - `convert()`
        """

        # TODO deliver


class TestDataObjectConverter:
    """Tests `DataObjectConverter().convert()`"""

    def test_no_relationships(self):
        """A resource without relationships"""

        mock_objs = [
            _get_mock_data_object(
                'B',
                str(i),
                attributes={
                    'happy_days': i
                }
            )
            for i in range(3)
        ]

        expected = {
            'data_too': [
                {
                    'type': 'B',
                    'id': str(i),
                    'attributes': {
                        'happy_days': i
                    }
                }
                for i in range(3)
            ]
        }

        converter = DataObjectConverter(data_key='data_too')
        observed = converter.convert_list(mock_objs)

        assert observed == expected

    def test_no_optional(self):
        """Optional fields not specified"""

        expected = {
            'data_free': {
                'type': 'hype'
            }
        }

        mock_obj = _get_mock_data_object('hype', None)
        converter = DataObjectConverter(data_key='data_free')
        observed = converter.convert(mock_obj)

        assert observed == expected

    def test_datetime(self):
        """
        All `datetime` attributes are formatted to `str`.

        No remaining attributes should be `datetime` valued.
        """

        mock_obj = _get_mock_data_object(
            'test',
            'lol',
            attributes={
                'a': datetime.now(),
                'b': datetime.now(),
                'c': True,
                'd': 'sdsa90d',
                'e': 394
            }
        )
        converter = DataObjectConverter()
        observed = converter.convert(mock_obj)

        attributes = observed['data']['attributes']
        assert list(attributes.keys()) == list('abcde')

        for c in 'abcde':
            assert not isinstance(attributes[c], datetime)

    def test_relationships(self):
        """
        A resource with relationships. Tests:
        - relationships
        - different `data_key` kwarg
        - `convert()`
        """

        # TODO deliver
