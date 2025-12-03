# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterable

from tol.core import DataObject, DataSource, core_data_object
from tol.core.operator import DetailGetter
from tol.validators import EnaSubmittableValidator


class _MockDataSource(DataSource, DetailGetter):

    def __init__(self, config: dict[str, Any]):
        super().__init__(config, [])

    def get_by_id(self):
        pass

    def get_one(self, object_type: str, object_id, **kwargs):
        if object_id == 'a':
            return None
        else:
            return self.data_object_factory(
                'submittable_taxon',
                object_id,
                attributes={
                    'submittable': True if object_id == 'b' else False
                }
            )

    @property
    def supported_types(self) -> list[str]:
        return ['submittable_taxon']


class TestEnaSubmittableValidator:

    def test_warning_and_error(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        mock_ds = _MockDataSource({})
        core_data_object(mock_ds)

        test_config = EnaSubmittableValidator.Config(
            field_name='key1',
        )

        validator = EnaSubmittableValidator(
            config=test_config,
            ena_datasource=mock_ds
        )

        list(
            validator.validate(mock_objs)
        )

        assert validator.results
        assert len(validator.errors) == 2
        assert len(validator.warnings) == 0
