# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Iterable

from tol.core import DataObject, DataSource
from tol.core.data_object_converter import DataObjectToDataObjectOrUpdateConverter
from tol.validators import ConvertorAndValidateValidator

# Converter that renames a field
# Validator that asserts a field exists


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


class TestConvertorAndValidateValidator:

    def test_all_ok(
        self,
        mock_objs: Iterable[DataObject],
        mock_data_source: DataSource
    ) -> None:

        config = ConvertorAndValidateValidator.Config(
            converters=[{
                'module': 'test.unit.validators.test_convertor_and_validate',
                'class_name': 'TestConverter',
                'config': {
                    'original_field_name': 'key1',
                    'new_field_name': 'key1_renamed',
                }
            }],
            validators=[{
                'module': 'tol.validators.allowed_keys',
                'class_name': 'AllowedKeysValidator',
                'config': {
                    'allowed_keys': [
                        'key1_renamed', 'key2', 'key3', 'key4', 'key5', 'key6', 'key7'
                    ],
                }
            }]
        )
        validator = ConvertorAndValidateValidator(
            config=config,
            data_object_factory=mock_data_source.data_object_factory,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert not validator.results

    def test_errors(
        self,
        mock_objs: Iterable[DataObject],
        mock_data_source: DataSource
    ) -> None:

        config = ConvertorAndValidateValidator.Config(
            converters=[{
                'module': 'test.unit.validators.test_convertor_and_validate',
                'class_name': 'TestConverter',
                'config': {
                    'original_field_name': 'key1',
                    'new_field_name': 'key1_renamed',
                }
            }],
            validators=[{
                'module': 'tol.validators.allowed_keys',
                'class_name': 'AllowedKeysValidator',
                'config': {
                    'allowed_keys': ['key1', 'key2', 'key3', 'key4', 'key5', 'key6', 'key7'],
                }
            }]
        )

        validator = ConvertorAndValidateValidator(
            config=config,
            data_object_factory=mock_data_source.data_object_factory,
        )

        validator = ConvertorAndValidateValidator(
            config=config,
            data_object_factory=mock_data_source.data_object_factory,
        )

        # consume the `Iterable`
        list(
            validator.validate(mock_objs)
        )

        assert len(validator.errors) == len(list(mock_objs))

    def test_multiple_converters_and_validators(
        self,
        mock_objs: Iterable[DataObject],
        mock_data_source: DataSource
    ) -> None:

        config = ConvertorAndValidateValidator.Config(
            converters=[
                {
                    'module': 'test.unit.validators.test_convertor_and_validate',
                    'class_name': 'TestConverter',
                    'config': {
                        'original_field_name': 'key1',
                        'new_field_name': 'key1_renamed',
                    }
                },
                {
                    'module': 'test.unit.validators.test_convertor_and_validate',
                    'class_name': 'TestConverter',
                    'config': {
                        'original_field_name': 'key1_renamed',
                        'new_field_name': 'key1_renamed2',
                    }
                },
            ],
            validators=[
                {
                    'module': 'tol.validators.allowed_keys',
                    'class_name': 'AllowedKeysValidator',
                    'config': {
                        'allowed_keys': [
                            'key1_renamed', 'key2', 'key3', 'key4', 'key5', 'key6', 'key7'
                        ],
                    }
                },
                {
                    'module': 'tol.validators.allowed_keys',
                    'class_name': 'AllowedKeysValidator',
                    'config': {
                        'allowed_keys': [
                            'key1_renamed2', 'key2', 'key3', 'key4', 'key5', 'key6', 'key7'
                        ],
                    }
                }
            ]
        )

        validator = ConvertorAndValidateValidator(
            config=config,
            data_object_factory=mock_data_source.data_object_factory,
        )

        list(validator.validate(mock_objs))

        # Aggregated results across multiple validators should still be empty
        assert len(validator.warnings) == 0
        assert len(validator.errors) == 3
        assert len(validator.results) == 3
