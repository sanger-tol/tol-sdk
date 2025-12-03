# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterable

from tol.core import DataObject, DataSource, core_data_object
from tol.core.operator import DetailGetter
from tol.validators import StsFieldsValidator


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
                            'data_input_key': 'key1',
                            'in_manifest': True,
                            'mandatory_input': True,
                            'allowed_values': ['b', 'c'],
                            'min': None,
                            'max': None,
                        }, {
                            'data_input_key': 'key5',
                            'in_manifest': True,
                            'mandatory_input': True,
                            'allowed_values': None,
                            'min': 0,
                            'max': 15,
                        }, {
                            'data_input_key': 'key6',
                            'in_manifest': True,
                            'mandatory_input': True,
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


class TestStsFieldsValidator:

    def test_warning_and_error(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        mock_ds = _MockDataSource({})
        core_data_object(mock_ds)

        test_config = StsFieldsValidator.Config(
            project_code='PROJ',
        )

        validator = StsFieldsValidator(
            config=test_config,
            datasource=mock_ds
        )

        list(
            validator.validate(mock_objs)
        )

        assert validator.results
        assert len(validator.errors) == 3
        assert len(validator.warnings) == 0
