# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from types import SimpleNamespace
from unittest import TestCase

from tol.flows.converters import (
    StsSampleToCasmBenchlingConverterFactory
)


class TestStsSampleToCasmBenchlingConverterFactory(TestCase):

    def _factory(self, mode='staging'):
        factory = object.__new__(StsSampleToCasmBenchlingConverterFactory)
        factory.mode = mode
        return factory

    def _sample(self, manifest_type):
        return SimpleNamespace(
            id='sample-id',
            attributes={},
            manifest=SimpleNamespace(manifest_type=manifest_type),
        )

    def _resolved_transfer_container_attribute(self, factory, sample):
        converter_class = factory.get_converter_class()
        converter = object.__new__(converter_class)
        object_map = factory.object_map_for_sample('transfer', sample)

        converter._populate_polymorphic_benchling_relationships(sample, object_map)

        return object_map['attribute_map']['destination_container_id']

    def test_transfer_container_type_is_sample_specific_for_mixed_manifests(self):
        factory = self._factory()
        rack_tube_sample = self._sample('RACK_TUBE')
        plate_well_sample = self._sample('PLATE_WELL')

        self.assertEqual(
            self._resolved_transfer_container_attribute(factory, rack_tube_sample),
            'casm_tube',
        )
        self.assertEqual(
            self._resolved_transfer_container_attribute(factory, plate_well_sample),
            'casm_well',
        )
        self.assertEqual(
            factory.BENCHLING_OBJECT_MAP['staging']['transfer']['attribute_map'][
                'destination_container_id'
            ],
            'container',
        )

    def test_transfer_container_type_is_sample_specific_in_reverse_order(self):
        factory = self._factory()
        rack_tube_sample = self._sample('RACK_TUBE')
        plate_well_sample = self._sample('PLATE_WELL')

        self.assertEqual(
            self._resolved_transfer_container_attribute(factory, plate_well_sample),
            'casm_well',
        )
        self.assertEqual(
            self._resolved_transfer_container_attribute(factory, rack_tube_sample),
            'casm_tube',
        )
        self.assertEqual(
            factory.BENCHLING_OBJECT_MAP['staging']['transfer']['attribute_map'][
                'destination_container_id'
            ],
            'container',
        )
