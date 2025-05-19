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


@pytest.fixture
def out_object() -> DataObject:
    return create_autospec(
        DataObject,
    )


@pytest.fixture
def data_object_factory(
    out_object: DataObject,
) -> DataObjectFactory:

    factory = create_autospec(
        DataObjectFactory,
        spec_set=True,
    )
    factory.return_value = out_object

    return factory


class TestYamlConverterLoading:

    def test_good(
        self,
        data_object_factory: DataObjectFactory,
        in_object: DataObject,
        out_object: DataObject,
    ) -> None:

        converter = YamlConverter(
            data_object_factory,
            'unit/core/yaml/good.yaml',
        )

        expected = [out_object]

        observed = list(
            converter.convert_iterable([in_object])
        )

        assert observed == expected

        data_object_factory.assert_called_once_with(
            'tos',
            id_='42',
            attributes={
                'sexual_system': 'i|d|k',
                'sex_determination': 'shrug:-:too'
            }
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
