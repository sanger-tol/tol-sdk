# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from pydantic import ValidationError

import pytest

from tol.core import DataObjectFactory
from tol.core.yaml import YamlConverter


@pytest.fixture
def data_object_factory() -> DataObjectFactory:
    return create_autospec(
        DataObjectFactory,
        spec_set=True,
    )


class TestYamlConverterLoading:

    def test_good(
        self,
        data_object_factory: DataObjectFactory,
    ) -> None:

        YamlConverter(
            data_object_factory,
            'core/yaml/good.yaml',
        )

    def test_bad(
        self,
        data_object_factory: DataObjectFactory,
    ) -> None:

        with pytest.raises(ValidationError):
            YamlConverter(
                data_object_factory,
                'core/yaml/bad.yaml',
            )
