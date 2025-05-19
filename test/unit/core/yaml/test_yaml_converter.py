# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import create_autospec

from pydantic import ValidationError

import pytest

from tol.core import (
    DataObject,
    DataObjectFactory,
)
from tol.core.yaml import YamlConverter


@pytest.fixture
def data_object_factory() -> DataObjectFactory:
    return create_autospec(
        DataObjectFactory,
        spec_set=True,
    )


@pytest.fixture
def in_object() -> DataObject:
    obj: DataObject = create_autospec(DataObject)

    obj.type = 'tos'
    obj.id = '42'

    attributes = {
        'gonochorous': 'i',
        'parthenogenetic': 'd',
        'hermaphrodite': 'k',
        'arrhenotoky': 'shrug',
        'paternal_genome_elimination': 'too',
    }

    obj.attributes = attributes
    for k, v in attributes.items():
        setattr(obj, k, v)

    return obj


class TestYamlConverterLoading:

    def test_good(
        self,
        data_object_factory: DataObjectFactory,
        in_object: DataObject,
    ) -> None:

        converter = YamlConverter(
            data_object_factory,
            'unit/core/yaml/good.yaml',
        )

        observed = list(
            converter.convert_iterable([in_object])
        )


    def test_bad(
        self,
        data_object_factory: DataObjectFactory,
    ) -> None:

        with pytest.raises(ValidationError):
            YamlConverter(
                data_object_factory,
                'unit/core/yaml/bad.yaml',
            )
