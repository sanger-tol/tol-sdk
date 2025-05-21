# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pathlib
from unittest.mock import create_autospec

from pydantic import ValidationError

import pytest

from tol.core import (
    DataObject,
    DataObjectFactory,
)
from tol.treeofsex import TOSConverter


BASE_DIR = pathlib.Path(__file__).parent.resolve()


@pytest.fixture
def in_object() -> DataObject:
    obj: DataObject = create_autospec(DataObject)

    obj.type = 'tos'
    obj.id = '42'

    attributes = {
        'sexual_system_in': 'X:-:Y:-:map_from:-:UN_MENTIONED',
        'include_only_strings': '1-_-2-_-LOL-_-3',
    }

    obj.attributes = attributes
    for k, v in attributes.items():
        setattr(obj, k, v)

    return obj


@pytest.fixture
def out_object() -> DataObject:
    return create_autospec(DataObject)


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


class TestTOSConverter:

    def test_good(
        self,
        data_object_factory: DataObjectFactory,
        in_object: DataObject,
        out_object: DataObject,
    ) -> None:
        """
        Converted according to the (correctly-structured)
        `good.yaml`.
        """

        good_path = BASE_DIR / 'good.yaml'

        converter = TOSConverter(
            data_object_factory,
            good_path,
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
                'sexual_system': 'X:-:Y:-:map_TO',
                'include_only_strings': '1-_-2-_-3',
            },
        )

    def test_bad(
        self,
        data_object_factory: DataObjectFactory,
    ) -> None:
        """
        Badly-structured `bad.yaml` leads to a Pydantic
        `ValidationError` being raised.
        """

        bad_path = BASE_DIR / 'bad.yaml'

        with pytest.raises(ValidationError):
            TOSConverter(
                data_object_factory,
                bad_path,
            )
