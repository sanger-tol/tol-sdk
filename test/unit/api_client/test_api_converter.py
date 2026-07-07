# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import date, datetime
from typing import Any, Optional
from unittest.mock import Mock, create_autospec

from tol.api_client.converter import (
    DataObjectConverter,
    JsonApiConverter
)
from tol.api_client.parser import DefaultParser
from tol.core import DataObject, DataSource
from tol.core.data_source_dict import DataSourceDict


def _get_mock_data_object(
    type_: str,
    id_: Optional[str],
    attributes: dict[str, Any] = {},
    to_one: dict[str, Any] = {},
    to_many: dict[str, Any] = {},
    provenance_: dict[str, Any] = {}
) -> DataObject:

    data_object = Mock()

    data_object.type = type_
    data_object.id = id_
    data_object.attributes = attributes
    data_object._to_one_objects = to_one
    data_object._to_many_objects = to_many
    data_object.provenance = provenance_

    return data_object


def _get_mock_data_source(
    attribute_types: dict[str, dict[str, Any]] = {}
) -> DataSource:

    mock_ds = create_autospec(DataSource, spec_set=True)

    mock_ds.attribute_types = attribute_types
    mock_ds.supported_types = list(attribute_types.keys())
    mock_ds.data_object_factory = _get_mock_data_object

    return mock_ds


def _get_mock_ds_dict(
    attribute_types: dict[str, dict[str, Any]] = {}
) -> dict[str, DataSource]:

    return DataSourceDict(
        _get_mock_data_source(attribute_types=attribute_types)
    )


class TestJsonApiConverter:
    """Tests `JsonApiConverter().convert()`"""

    def test_no_relationships(self):
        """A resource without relationships"""

        in_ = {
            'data': [
                {
                    'type': 'A',
                    'id': str(i),
                    'attributes': {
                        'int_I': i,
                        'provenance': {
                            'int_I': {
                                'source_1': i,
                                'source_2': i + 1
                            }
                        }
                    }
                }
                for i in range(4)
            ]
        }

        parser = DefaultParser(_get_mock_ds_dict({'A': {'int_I': 'int'}}))
        converter = JsonApiConverter(parser)
        (out_, _) = converter.convert_list(in_)

        assert len(out_) == 4
        for i in range(4):
            out_i = out_[i]
            assert out_i.type == 'A'
            assert out_i.id == str(i)
            assert out_i.attributes == {'int_I': i}
            assert out_i.provenance == {
                'int_I': {
                    'source_1': i,
                    'source_2': i + 1
                }
            }

    def test_no_optional(self):
        """Optional fields not specified"""

        in_ = {'data': {'type': 'hype'}}
        parser = DefaultParser(_get_mock_ds_dict({'hype': {}}))
        converter = JsonApiConverter(parser)
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
                    'd': now,
                    'provenance': {
                        'a': {
                            'source_1': now,
                            'source_2': now
                        }
                    }
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

        parser = DefaultParser(
            _get_mock_ds_dict(attribute_types=attribute_types)
        )

        converter = JsonApiConverter(parser)

        observed = converter.convert(in_)

        for c in 'abc':
            assert isinstance(
                observed.attributes[c],
                datetime
            )
        assert isinstance(observed.attributes['d'], str)
        assert isinstance(observed.provenance['a']['source_1'], datetime)
        assert isinstance(observed.provenance['a']['source_2'], datetime)

    def test_count(self):

        in_ = {
            'meta': {
                'total': 123
            }
        }

        attribute_types = {
            'test': {
                'a': 'datetime',
                'd': 'str'
            }
        }

        parser = DefaultParser(
            _get_mock_ds_dict(attribute_types=attribute_types)
        )

        converter = JsonApiConverter(parser)

        observed = converter.convert_count(in_)

        assert observed == 123

    def test_stats(self):
        """
        All `datetime` attributes, as defined in
        `ApiDataSource().attribute_types`, are parsed.
        """
        now_datetime = datetime.now()
        now = str(now_datetime)

        in_ = {
            'meta': {
                'type': 'test',
                'stats': {
                    'a': {
                        'min': now,
                        'max': now,
                        'unique': 16
                    },
                    'd': {
                        'min': 'aaa',
                        'max': 'zzz',
                        'unique': 20
                    }
                }
            }
        }

        attribute_types = {
            'test': {
                'a': 'datetime',
                'd': 'str'
            }
        }

        parser = DefaultParser(
            _get_mock_ds_dict(attribute_types=attribute_types)
        )

        converter = JsonApiConverter(parser)

        observed = converter.convert_stats(in_)

        assert observed['stats']['a']['min'] == now_datetime
        assert observed['stats']['a']['max'] == now_datetime
        assert observed['stats']['a']['unique'] == 16
        assert observed['stats']['d']['min'] == 'aaa'
        assert observed['stats']['d']['max'] == 'zzz'
        assert observed['stats']['d']['unique'] == 20


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
                },
                provenance_={
                    'happy_days': {
                        'source_1': i,
                        'source_2': i + 1
                    }
                }
            )
            for i in range(3)
        ]

        expected = {
            'data': [
                {
                    'type': 'B',
                    'id': str(i),
                    'attributes': {
                        'happy_days': i,
                        'provenance': {
                            'happy_days': {
                                'source_1': i,
                                'source_2': i + 1
                            }
                        }
                    }
                }
                for i in range(3)
            ]
        }

        converter = DataObjectConverter(_get_mock_data_source())
        observed = converter.convert_list(mock_objs)

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
                'b': date.today(),
                'c': True,
                'd': 'sdsa90d',
                'e': 394
            }
        )
        converter = DataObjectConverter(_get_mock_data_source())
        observed = converter.convert(mock_obj)

        attributes = observed['data']['attributes']
        assert list(attributes.keys()) == list('abcde')

        for c in 'abcde':
            assert not isinstance(attributes[c], date)
