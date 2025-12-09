# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Iterable

from tol.core import DataObject
from tol.validators import AllowedValuesFromDataSourceValidator


class TestAllowedValuesFromDataSourceValidator:

    def test_warning_and_error(
        self,
        mock_objs: Iterable[DataObject]
    ) -> None:

        test_config = AllowedValuesFromDataSourceValidator.Config(
            datasource_instance_id=1,
            datasource_object_type='test',
            datasource_field_name='test',
            field_name='key1',
        )

        validator = AllowedValuesFromDataSourceValidator(
            config=test_config,
            allowed_values=['a', 'b', 1, 2, 3],
        )

        list(
            validator.validate(mock_objs)
        )

        assert validator.results
        assert len(validator.errors) == 1
        assert len(validator.warnings) == 0
        assert validator.errors[0].detail == (
            'The value of the field key1 must be one of a, b, 1, 2 or 3 (found value c)'
        )
