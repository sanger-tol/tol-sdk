# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from tol.core import DataObject, DataSource
from tol.core.data_object_converter import DataObjectToDataObjectOrUpdateConverter
from tol.flows.converters import MultipleConverter

# Converter that renames a field


class TestConverter(
    DataObjectToDataObjectOrUpdateConverter
):
    @dataclass(slots=True, frozen=True, kw_only=True)
    class Config:
        original_field_name: str
        new_field_name: str

    def __init__(self, data_object_factory, config: Config):
        # No-op; just satisfy expected signature
        self._config = config

    def convert(
        self,
        data_object: DataObject
    ) -> Iterable[DataObject]:
        value = data_object.get_field_by_name(self._config.original_field_name)
        if value is not None:
            data_object.attributes[self._config.new_field_name] = value
            del data_object.attributes[self._config.original_field_name]
        yield data_object


class TestMultipleConverter:

    def test_multiple_converters(
        self,
        mock_objs: Iterable[DataObject],
        mock_data_source: DataSource
    ) -> None:

        config = MultipleConverter.Config(
            converters=[
                {
                    'module': 'test.unit.converter.test_multiple_converter',
                    'class_name': 'TestConverter',
                    'config_details': {
                        'original_field_name': 'key1',
                        'new_field_name': 'key1_renamed',
                    }
                },
                {
                    'module': 'test.unit.converter.test_multiple_converter',
                    'class_name': 'TestConverter',
                    'config_details': {
                        'original_field_name': 'key1_renamed',
                        'new_field_name': 'key1_renamed2',
                    }
                },
            ]
        )

        multiple_converter = MultipleConverter(
            config=config,
            data_object_factory=mock_data_source.data_object_factory,
        )

        ret = list(multiple_converter.convert_iterable(mock_objs))

        assert len(ret) == 3
        for obj in ret:
            assert 'key1' not in obj.attributes
            assert 'key1_renamed' not in obj.attributes
            assert 'key1_renamed2' in obj.attributes
            assert obj.attributes['key1_renamed2'] in 'abc'
