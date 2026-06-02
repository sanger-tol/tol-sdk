# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

import pytest

from tol.core import (
    ChainedConverter,
    DefaultDataObjectToDataObjectConverter,
)
from tol.flows.converters import (
    ElasticObjectToBenchlingWorklistItemConverter,
    ElasticSampleToBenchlingTissueConverter,
)


@pytest.fixture
def make_worklist():
    def _make(worklist_type: str) -> MagicMock:
        wl = MagicMock()
        wl.worklist_type = worklist_type
        return wl
    return _make


@pytest.fixture
def converter_types():
    def _get(converter) -> list[type]:
        return [type(c) for c in converter._chain._ChainedConverter__converters]
    return _get


def _build(object_type, worklist, data_object_factory=None):
    return ElasticObjectToBenchlingWorklistItemConverter(
        data_object_factory or MagicMock(),
        config=ElasticObjectToBenchlingWorklistItemConverter.Config(
            object_type=object_type,
            worklist=worklist,
        )
    )


class TestElasticObjectToBenchlingWorklistItemConverter:

    def test_bioentity_worklist_with_sample_uses_tissue_converter(
        self, make_worklist, converter_types
    ):
        converter = _build('sample', make_worklist('bioentity'))

        assert isinstance(converter._chain, ChainedConverter)
        assert converter_types(converter)[0] is ElasticSampleToBenchlingTissueConverter

    def test_bioentity_worklist_with_non_sample_uses_default_converter(
        self, make_worklist, converter_types
    ):
        converter = _build('extraction', make_worklist('bioentity'))

        assert converter_types(converter)[0] is DefaultDataObjectToDataObjectConverter

    def test_extraction_container_uses_default_converter_regardless_of_worklist_type(
        self, make_worklist, converter_types
    ):
        converter = _build('extraction_container', make_worklist('container'))

        assert converter_types(converter)[0] is DefaultDataObjectToDataObjectConverter

    def test_container_worklist_uses_default_converter(
        self, make_worklist, converter_types
    ):
        converter = _build('sample', make_worklist('container'))

        assert converter_types(converter)[0] is DefaultDataObjectToDataObjectConverter

    def test_always_ends_with_worklist_item_converter(self, make_worklist):
        for worklist_type in ('bioentity', 'container'):
            converter = _build('sample', make_worklist(worklist_type))
            last = converter._chain._ChainedConverter__converters[-1]
            assert type(last).__name__ == 'BenchlingEntityToBenchlingWorklistItemConverter'

    def test_object_type_mapping_selects_correct_destination(
        self, make_worklist, converter_types
    ):
        # 'extraction' maps to 'dna_extract' — DefaultDataObjectToDataObjectConverter is used
        converter = _build('extraction', make_worklist('bioentity'))

        assert converter_types(converter)[0] is DefaultDataObjectToDataObjectConverter

    def test_config_is_accessible(self, make_worklist):
        wl = make_worklist('bioentity')
        converter = _build('sample', wl)

        assert converter.config.object_type == 'sample'
        assert converter.config.worklist is wl
