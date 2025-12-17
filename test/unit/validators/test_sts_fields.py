# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime, timedelta
from typing import Any, Iterable

import pytest

from tol.core import DataObject, DataSource, core_data_object
from tol.core.operator import DetailGetter
from tol.validators import StsFieldsValidator


@pytest.fixture
def mock_sts() -> DataSource:
    class _MockDataSource(DataSource, DetailGetter):

        def __init__(self, config: dict[str, Any]):
            super().__init__(config, [])

        def get_by_id(self):
            pass

        def get_one(self, object_type: str, object_id, **kwargs):
            return self.data_object_factory(
                'project',
                object_id,
                attributes={
                    'template': {
                        'data_fields': [
                            {
                                'type': 'String',
                                'data_input_key': 'key1',
                                'in_manifest': True,
                                'mandatory_validation': True,
                                'allowed_values': [
                                    {'id': 'b', 'value': 'b'}, {'id': 'c', 'value': 'c'}
                                ],
                                'min': None,
                                'max': None,
                            }, {
                                'type': 'TextArea',
                                'data_input_key': 'key5',
                                'in_manifest': True,
                                'mandatory_validation': True,
                                'allowed_values': None,
                                'min': 0,
                                'max': 15,
                            }, {
                                'type': 'Date',
                                'data_input_key': 'key8',
                                'in_manifest': True,
                                'mandatory_validation': True,
                                'allowed_values': None,
                                'range_limit': True,
                                'min': 30,
                                'max': 30,
                            }, {
                                'type': 'Decimal',
                                'data_input_key': 'key9',
                                'in_manifest': True,
                                'mandatory_validation': True,
                                'allowed_values': None,
                                'min': 0,
                                'max': 10,
                            }, {
                                'type': 'Integer',
                                'data_input_key': 'key11',
                                'in_manifest': True,
                                'mandatory_validation': True,
                                'allowed_values': None,
                                'min': 0,
                                'max': 12,
                            }, {
                                'type': 'Boolean',
                                'data_input_key': 'key13',
                                'in_manifest': True,
                                'mandatory_validation': True,
                                'allowed_values': None,
                                'min': None,
                                'max': None,
                            }, {
                                'status': 'Inactive',
                                'type': 'Boolean',
                                'data_input_key': 'key_inactive',
                                'in_manifest': True,
                                'mandatory_input': True,
                                'allowed_values': None,
                                'min': None,
                                'max': None,
                            }, {
                                'status': 'Active',
                                'type': 'Boolean',
                                'data_input_key': 'key_optional',
                                'in_manifest': True,
                                'mandatory_input': False,
                                'allowed_values': None,
                                'min': None,
                                'max': None,
                            },
                        ]
                    }
                }
            )

        @property
        def supported_types(self) -> list[str]:
            return ['project']

    mock_ds = _MockDataSource({})
    core_data_object(mock_ds)
    return mock_ds


@pytest.fixture
def validator(mock_sts: DataSource) -> StsFieldsValidator:
    test_config = StsFieldsValidator.Config(
        project_code='PROJ',
    )

    validator = StsFieldsValidator(
        config=test_config,
        datasource=mock_sts
    )
    return validator


class TestStsFieldsValidator:

    def test_warning_and_error(
        self,
        validator: StsFieldsValidator,
        mock_objs: Iterable[DataObject]
    ) -> None:

        list(
            validator.validate(mock_objs)
        )

        assert validator.results
        assert len(validator.errors) == 7
        assert len(validator.warnings) == 0

    def test_invalid_date_type(
        self,
        validator: StsFieldsValidator,
        mock_data_source: DataSource
    ) -> None:
        obj = mock_data_source.data_object_factory(
            'upload',
            'sample1',
            attributes={
                'key1': 'b',
                'key5': 'x' * 10,
                'key8': 'abc',  # Invalid date
                'key9': 5.0,
                'key11': 10,
                'key13': 'Y',
            }
        )
        list(
            validator.validate([obj])
        )
        assert len(validator.errors) == 1

    def test_invalid_string_type(
        self,
        validator: StsFieldsValidator,
        mock_data_source: DataSource
    ) -> None:
        obj = mock_data_source.data_object_factory(
            'upload',
            'sample1',
            attributes={
                'key1': 1,  # Invalid string
                'key5': 'x' * 10,
                'key8': datetime.now() - timedelta(days=20),
                'key9': 5.0,
                'key11': 10,
                'key13': 'Y',
            }
        )
        list(
            validator.validate([obj])
        )
        assert len(validator.errors) == 2  # Also not in allowed_values

    def test_invalid_integer_type(
        self,
        validator: StsFieldsValidator,
        mock_data_source: DataSource
    ) -> None:
        obj = mock_data_source.data_object_factory(
            'upload',
            'sample1',
            attributes={
                'key1': 'b',
                'key5': 'x' * 10,
                'key8': datetime.now() - timedelta(days=20),
                'key9': 5.0,
                'key11': '10',
                'key13': 'Y',
            }
        )
        list(
            validator.validate([obj])
        )
        assert len(validator.errors) == 1

    def test_invalid_decimal_type(
        self,
        validator: StsFieldsValidator,
        mock_data_source: DataSource
    ) -> None:
        obj = mock_data_source.data_object_factory(
            'upload',
            'sample1',
            attributes={
                'key1': 'b',
                'key5': 'x' * 10,
                'key8': datetime.now() - timedelta(days=20),
                'key9': '5.0',
                'key11': 10,
                'key13': 'Y',
            }
        )
        list(
            validator.validate([obj])
        )
        assert len(validator.errors) == 1

    def test_integer_out_of_range(
        self,
        validator: StsFieldsValidator,
        mock_data_source: DataSource
    ) -> None:
        # Date field invalid
        obj = mock_data_source.data_object_factory(
            'upload',
            'sample1',
            attributes={
                'key1': 'b',
                'key5': 'x' * 10,
                'key8': datetime.now() - timedelta(days=20),  # In range
                'key9': 5.0,
                'key11': 20,
                'key13': 'Y',
            }
        )
        list(
            validator.validate([obj])
        )
        assert len(validator.errors) == 1