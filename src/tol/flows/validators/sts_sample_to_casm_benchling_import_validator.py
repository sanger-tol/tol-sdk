# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import copy
import re
from collections.abc import Iterable as IterableABC
from typing import Any, Iterable, Optional, TypedDict

from benchling_sdk.errors import BenchlingError
from pydantic import BaseModel, Field

from tol.core import DataObject, DataSourceFilter, ErrorObject
from tol.flows.converters.sts_sample_to_casm_benchling_converter import (
    StsSampleToCasmBenchlingConverterFactory,
)
from tol.sources.benchling import benchling


class Attribute(TypedDict, total=False):
    object_type: str
    sts_identifier: str
    benchling_identifier: str
    sts_value: Any
    benchling_value: Any
    passed: bool
    failed_reason: Optional[str]


class ValidateObject(BaseModel):
    sample_id: str = Field(
        description='ID of the sample within the STS database'
    )
    attributes: dict[str, Attribute] = Field(
        default_factory=dict,
        description='Dictionary of validated sample attributes',
    )
    big_errors: list[str] = Field(
        default_factory=list,
        description='Larger errors affecting the sample',
    )


def validation_errors(validation_object: ValidateObject) -> list[dict[str, Any]]:
    """Return all failed validation details for one sample.

    Args:
        validation_object: Validation result for a single STS sample.

    Returns:
        list[dict[str, Any]]: Field-level and sample-level validation errors.
    """
    errors: list[dict[str, Any]] = [
        {
            'field': attr.get('sts_identifier'),
            'benchling_field': attr.get('benchling_identifier'),
            'object_type': attr.get('object_type'),
            'reason': attr.get('failed_reason'),
            'sts_value': attr.get('sts_value'),
            'benchling_value': attr.get('benchling_value'),
        }
        for attr in validation_object.attributes.values()
        if attr.get('passed') is False
    ]
    errors.extend(
        {
            'field': None,
            'benchling_field': None,
            'object_type': None,
            'reason': error,
            'sts_value': None,
            'benchling_value': None,
        }
        for error in validation_object.big_errors
    )
    return errors


def validation_failed(validation_object: ValidateObject) -> bool:
    """Determine whether a sample validation result contains any errors.

    Args:
        validation_object: Validation result for a single STS sample.

    Returns:
        bool: True when field-level or sample-level errors are present.
    """
    return bool(validation_errors(validation_object))


def failed_validation_objects(
        validation_objects: Iterable[ValidateObject]
) -> list[ValidateObject]:
    """Filter validation results to the samples that failed validation.

    Args:
        validation_objects: Validation results to inspect.

    Returns:
        list[ValidateObject]: Validation results that contain errors.
    """
    return [
        validation_object
        for validation_object in validation_objects
        if validation_failed(validation_object)
    ]


class StsSampleToCasmBenchlingImportValidator:
    STS_OBJECT_MAP = StsSampleToCasmBenchlingConverterFactory.STS_OBJECT_MAP
    BENCHLING_OBJECT_MAP = StsSampleToCasmBenchlingConverterFactory.BENCHLING_OBJECT_MAP
    CONCATENATED_VALUES = StsSampleToCasmBenchlingConverterFactory.CONCATENATED_VALUES
    VALUE_REPLACEMENTS = StsSampleToCasmBenchlingConverterFactory.VALUE_REPLACEMENTS
    COMPUTED_VALUES = StsSampleToCasmBenchlingConverterFactory.COMPUTED_VALUES
    DESTINATION_OBJECT_TYPES = StsSampleToCasmBenchlingConverterFactory.DESTINATION_OBJECT_TYPES
    BOX_PLATE_SCHEMA_FIELD = (
        StsSampleToCasmBenchlingConverterFactory.BOX_PLATE_SCHEMA_FIELD
    )
    RACK_TUBE_MANIFEST_TYPE = (
        StsSampleToCasmBenchlingConverterFactory.RACK_TUBE_MANIFEST_TYPE
    )
    MULTISELECT_BENCHLING_RELATIONSHIPS = (
        StsSampleToCasmBenchlingConverterFactory.MULTISELECT_BENCHLING_RELATIONSHIPS
    )

    BENCHLING_OBJECT_TYPES_TO_VALIDATE = {
        'production': [
            'box_or_plate',
            'container',
            'casm_donor_v1',
            'casm_tissue_v1',
            'casm_sample_metadata_v1',
            'casm_sample_v1',
            'casm_qc_result_v1',
            'casm_programme_id_v1',
            'casm_sample_status_v1',
            'transfer',
        ],
        'staging': [
            'box_or_plate',
            'container',
            'casm_donor',
            'casm_tissue',
            'casm_sample_metadata',
            'casm_sample',
            'casm_qc_result',
            'casm_programme_id',
            'casm_sample_status',
            'transfer',
        ],
    }

    def __init__(
            self,
            mode: str = 'staging',
            benchling_ds=None,
    ):
        """Initialize the CASM Benchling import validator.

        Args:
            mode: CASM converter mode, either staging or production.
            benchling_ds: Optional Benchling data source override for lookups.

        Raises:
            ValueError: If mode is not staging or production.
        """
        if mode not in ['staging', 'production']:
            raise ValueError('Mode must be either "production" or "staging"')

        self.mode = mode
        self.benchling = benchling_ds or benchling()
        self._stored_values: dict[str, dict[str, Any]] = {}
        self._planned_values: dict[str, set[str]] = {}

    def validate_iterable(
            self,
            inputs: Iterable[DataObject],
    ) -> list[ValidateObject]:
        """Validate an iterable of STS samples for CASM Benchling import readiness.

        Args:
            inputs: STS sample data objects to validate.

        Returns:
            list[ValidateObject]: Validation results keyed by sample id.
        """
        samples = list(inputs)
        validation_objects = {
            str(sample.id): ValidateObject(sample_id=str(sample.id))
            for sample in samples
        }

        self._reset_run_state()
        self._validate_box_plate_schema_by_rack(samples, validation_objects)

        for benchling_object_type in self.BENCHLING_OBJECT_TYPES_TO_VALIDATE[self.mode]:
            for sample in samples:
                self._validate_stage(
                    sample,
                    validation_objects[str(sample.id)],
                    benchling_object_type,
                )

        return list(validation_objects.values())

    def to_error_objects(
            self,
            validation_objects: Iterable[ValidateObject],
            loader_name: str = 'Benchling Preflight Validation',
    ) -> list[ErrorObject]:
        """Convert failed validation results into STS loader error objects.

        Args:
            validation_objects: Validation results to convert.
            loader_name: Loader name to include in error details.

        Returns:
            list[ErrorObject]: Error objects for samples that failed validation.
        """
        errors: list[ErrorObject] = []

        for validation_object in failed_validation_objects(validation_objects):
            validation_error_details = validation_errors(validation_object)
            message = '; '.join(
                str(error['reason'])
                for error in validation_error_details
                if error.get('reason')
            )
            errors.append(
                ErrorObject(
                    details={
                        'exception_type': 'ValidationError',
                        'message': message,
                        'stage': 'validation',
                        'loader': loader_name,
                        'source_object_type': 'sample',
                        'source_object_id': validation_object.sample_id,
                        'validation_errors': validation_error_details,
                    },
                    object_type='sample',
                    object_id=validation_object.sample_id,
                )
            )

        return errors

    def _reset_run_state(self) -> None:
        """Reset cached Benchling and planned values for a validation run."""
        self._stored_values = {
            object_type: dict(object_map.get('stored_values', {}))
            for object_type, object_map in self.BENCHLING_OBJECT_MAP[self.mode].items()
        }
        self._planned_values = {
            object_type: set()
            for object_type in self.BENCHLING_OBJECT_MAP[self.mode]
        }

    def _validate_box_plate_schema_by_rack(
            self,
            samples: list[DataObject],
            validation_objects: dict[str, ValidateObject],
    ) -> None:
        """Validate that rack-tube samples in the same rack share one schema value.

        Args:
            samples: STS sample data objects in the validation batch.
            validation_objects: Mutable validation results keyed by sample id.
        """
        samples_by_rack: dict[str, list[DataObject]] = {}

        for sample in samples:
            if (
                    StsSampleToCasmBenchlingConverterFactory.get_manifest_type(sample)
                    != self.RACK_TUBE_MANIFEST_TYPE
            ):
                continue

            rack_id = (
                StsSampleToCasmBenchlingConverterFactory.get_storage_rack_id(sample)
                or '<unknown>'
            )
            samples_by_rack.setdefault(str(rack_id), []).append(sample)

        for rack_id, rack_samples in samples_by_rack.items():
            values_by_sample_id = {
                str(sample.id): (
                    StsSampleToCasmBenchlingConverterFactory
                    .get_box_plate_schema_value(sample)
                )
                for sample in rack_samples
            }
            missing_values = [
                value
                for value in values_by_sample_id.values()
                if self._is_missing(value)
            ]
            present_values = sorted({
                str(value)
                for value in values_by_sample_id.values()
                if not self._is_missing(value)
            })

            if missing_values:
                self._add_rack_error(
                    rack_samples,
                    validation_objects,
                    f'Rack {rack_id} is missing {self.BOX_PLATE_SCHEMA_FIELD}',
                )

            if len(present_values) > 1:
                self._add_rack_error(
                    rack_samples,
                    validation_objects,
                    (
                        f'Rack {rack_id} has conflicting '
                        f'{self.BOX_PLATE_SCHEMA_FIELD} values: '
                        f'{", ".join(present_values)}'
                    ),
                )

    def _add_rack_error(
            self,
            rack_samples: list[DataObject],
            validation_objects: dict[str, ValidateObject],
            error: str,
    ) -> None:
        """Add a rack-level error to every sample in the rack.

        Args:
            rack_samples: Samples affected by the rack-level error.
            validation_objects: Mutable validation results keyed by sample id.
            error: Error message to add.
        """
        for sample in rack_samples:
            self._add_big_error_once(validation_objects[str(sample.id)], error)

    @staticmethod
    def _add_big_error_once(
            validation_object: ValidateObject,
            error: str,
    ) -> None:
        """Append a sample-level validation error if it is not already present.

        Args:
            validation_object: Validation result to update.
            error: Error message to add.
        """
        if error not in validation_object.big_errors:
            validation_object.big_errors.append(error)

    def _has_box_plate_schema_error(
            self,
            validation_object: ValidateObject,
    ) -> bool:
        """Check whether a validation result already has a box-plate schema error.

        Args:
            validation_object: Validation result to inspect.

        Returns:
            bool: True when the result contains a box-plate schema error.
        """
        return any(
            self.BOX_PLATE_SCHEMA_FIELD in error
            for error in validation_object.big_errors
        )

    def _validate_stage(
            self,
            sample: DataObject,
            validation_object: ValidateObject,
            benchling_object_type: str,
    ) -> None:
        """Validate one Benchling object stage for a sample.

        Args:
            sample: STS sample data object being validated.
            validation_object: Validation result to update.
            benchling_object_type: Static or dynamic Benchling object type to validate.
        """
        if (
                benchling_object_type in {'box_or_plate', 'container', 'transfer'}
                and self._has_box_plate_schema_error(validation_object)
        ):
            return

        resolved_object_type = self._resolve_destination_object_type(
            sample,
            validation_object,
            benchling_object_type,
        )
        if resolved_object_type is None:
            return

        try:
            object_map = self._object_map_for_sample(resolved_object_type, sample)
        except ValueError as exc:
            self._add_big_error_once(validation_object, str(exc))
            return

        if object_map is None:
            validation_object.big_errors.append(
                'Sample is not ready for import: Unsupported Benchling object '
                f'type {resolved_object_type}'
            )
            return

        stage_failed = False
        benchling_schema = self.get_benchling_schema(resolved_object_type)

        try:
            if self._does_object_exist(resolved_object_type, sample, object_map):
                self._mark_available(resolved_object_type, sample, object_map)
                self._record_existing_object(
                    validation_object,
                    resolved_object_type,
                    object_map,
                    sample,
                )
                return
        except Exception as exc:
            stage_failed = True
            validation_object.big_errors.append(str(exc))

        relationship_failed = self._populate_relationships(
            sample,
            object_map,
            validation_object,
            resolved_object_type,
        )
        attribute_failed = self._populate_object_attributes(
            object_map,
            sample,
            validation_object,
            benchling_schema,
            resolved_object_type,
        )

        if not stage_failed and not relationship_failed and not attribute_failed:
            self._mark_available(resolved_object_type, sample, object_map)

    def _resolve_destination_object_type(
            self,
            sample: DataObject,
            validation_object: ValidateObject,
            benchling_object_type: str,
    ) -> str | None:
        """Resolve a static or dynamic destination object type for a sample.

        Args:
            sample: STS sample data object being validated.
            validation_object: Validation result to update if resolution fails.
            benchling_object_type: Static object type or dynamic conversion alias.

        Returns:
            str | None: Destination object type, or None when validation should stop.
        """
        if benchling_object_type in self.BENCHLING_OBJECT_MAP[self.mode]:
            return benchling_object_type

        destination_object_types = self.DESTINATION_OBJECT_TYPES[self.mode].get(
            benchling_object_type,
            {},
        )
        manifest = getattr(sample, 'manifest', None)
        manifest_type = getattr(manifest, 'manifest_type', None)

        if manifest_type in destination_object_types:
            try:
                return (
                    StsSampleToCasmBenchlingConverterFactory
                    .destination_object_type_for_sample(
                        self.mode,
                        sample,
                        benchling_object_type,
                    )
                )
            except ValueError as exc:
                self._add_big_error_once(validation_object, str(exc))
                return None

        validation_object.big_errors.append(
            'Sample is not ready for import: Unsupported destination type '
            f'for dynamic conversion when trying to convert to {benchling_object_type}'
        )
        return None

    def _object_map_for_sample(
            self,
            benchling_object_type: str,
            sample: DataObject,
    ) -> dict[str, Any] | None:
        """Build an object map adjusted for the sample's dynamic relationships.

        Args:
            benchling_object_type: Destination Benchling object type.
            sample: STS sample data object being validated.

        Returns:
            dict[str, Any] | None: Sample-specific object map, or None if unsupported.

        Raises:
            ValueError: If dynamic box-plate schema selection fails.
        """
        if benchling_object_type not in self.BENCHLING_OBJECT_MAP[self.mode]:
            return None

        object_map = copy.deepcopy(
            self.BENCHLING_OBJECT_MAP[self.mode][benchling_object_type]
        )
        StsSampleToCasmBenchlingConverterFactory.apply_box_plate_schema_relationships(
            self.mode,
            benchling_object_type,
            sample,
            object_map,
        )
        self._populate_polymorphic_benchling_relationships(sample, object_map)
        return object_map

    def _record_existing_object(
            self,
            validation_object: ValidateObject,
            benchling_object_type: str,
            object_map: dict[str, Any],
            sample: DataObject,
    ) -> None:
        """Record a passing validation attribute for an existing Benchling object.

        Args:
            validation_object: Validation result to update.
            benchling_object_type: Destination Benchling object type.
            object_map: Object map used for primary attribute resolution.
            sample: STS sample data object being validated.
        """
        primary_attribute = object_map.get('primary_attribute')
        if primary_attribute is None:
            return

        mapped_attribute = object_map['attribute_map'][primary_attribute]
        value = self._get_object_primary_attribute_value(
            object_map,
            sample,
            benchling_object_type,
        )
        self._add_attribute(
            validation_object,
            object_type=benchling_object_type,
            sts_identifier=mapped_attribute,
            benchling_identifier=primary_attribute,
            sts_value=value,
            benchling_value=value,
            passed=True,
        )

    def _does_object_exist(
            self,
            destination_object_type: str,
            sample: DataObject,
            object_map: dict[str, Any],
    ) -> bool:
        """Check whether the destination object already exists or is planned.

        Args:
            destination_object_type: Benchling object type to look up.
            sample: STS sample data object being validated.
            object_map: Object map used for primary attribute resolution.

        Returns:
            bool: True when the object is available in Benchling or this import.
        """
        primary_attribute = object_map.get('primary_attribute')
        if primary_attribute is None:
            return False

        search_value = self._get_object_primary_attribute_value(
            object_map,
            sample,
            destination_object_type,
        )
        if self._is_missing(search_value):
            return False

        return self._relationship_available(
            object_type=destination_object_type,
            search_identifier=primary_attribute,
            search_value=search_value,
        )

    def _mark_available(
            self,
            benchling_object_type: str,
            sample: DataObject,
            object_map: dict[str, Any],
    ) -> None:
        """Mark an object value as planned for the current validation run.

        Args:
            benchling_object_type: Benchling object type being marked.
            sample: STS sample data object that produced the value.
            object_map: Object map used for primary attribute resolution.
        """
        primary_attribute = object_map.get('primary_attribute')
        if primary_attribute is None:
            return

        primary_value = self._get_object_primary_attribute_value(
            object_map,
            sample,
            benchling_object_type,
        )
        if not self._is_missing(primary_value):
            self._planned_values.setdefault(benchling_object_type, set()).add(
                str(primary_value)
            )

    def _populate_relationships(
            self,
            sample: DataObject,
            object_map: dict[str, Any],
            validation_object: ValidateObject,
            benchling_object_type: str,
    ) -> bool:
        """Validate required Benchling relationships for an object map.

        Args:
            sample: STS sample data object being validated.
            object_map: Object map describing required relationships.
            validation_object: Validation result to update.
            benchling_object_type: Destination Benchling object type.

        Returns:
            bool: True when at least one relationship validation failed.
        """
        failed = False
        self._populate_sts_relationships(sample, object_map)
        mapped_relationships = set(object_map.get('attribute_map', {}).values())

        for relationship_object_type in object_map.get('benchling_relationships', []):
            if relationship_object_type in mapped_relationships:
                continue

            attribute = self._build_attribute(
                object_type=benchling_object_type,
                sts_identifier=relationship_object_type,
                benchling_identifier=relationship_object_type,
            )
            self._check_benchling_relationship_available(
                sample,
                relationship_object_type,
                attribute,
            )
            self._add_attribute_from_dict(validation_object, attribute)
            failed = failed or attribute.get('passed') is False

        return failed

    def _populate_sts_relationships(
            self,
            sample: DataObject,
            object_map: dict[str, Any],
    ) -> None:
        """Populate sample attributes from configured STS relationships.

        Args:
            sample: STS sample data object to mutate.
            object_map: Object map listing STS relationships to resolve.
        """
        for relationship_object_identifier in object_map.get('sts_relationships', []):
            if sample.attributes.get(relationship_object_identifier) is None:
                sample.attributes[relationship_object_identifier] = (
                    self._get_sts_relationship_attribute_value(
                        relationship_object_identifier,
                        sample,
                    )
                )

    def _get_sts_relationship_attribute_value(
            self,
            relationship_object_identifier: str,
            sample: DataObject,
    ) -> Any:
        """Resolve the configured identifying value from an STS relationship.

        Args:
            relationship_object_identifier: STS relationship key in STS_OBJECT_MAP.
            sample: STS sample data object containing the relationship.

        Returns:
            Any: Relationship identifying value, or None when unavailable.
        """
        attribute_value = None
        relationship_object_map = self.STS_OBJECT_MAP[
            relationship_object_identifier
        ]
        sts_relationship = getattr(
            sample,
            relationship_object_map['relationship_identifier'],
            None,
        )

        if (
                isinstance(sts_relationship, IterableABC)
                and not isinstance(sts_relationship, str)
        ):
            relationship_object = next(iter(sts_relationship), None)
        else:
            relationship_object = sts_relationship

        if relationship_object is not None:
            attribute_value = getattr(
                relationship_object,
                relationship_object_map['identifier'],
                None,
            )

        return attribute_value

    def _populate_object_attributes(
            self,
            object_map: dict[str, Any],
            sample: DataObject,
            validation_object: ValidateObject,
            benchling_schema: dict[str, Any],
            benchling_object_type: str,
    ) -> bool:
        """Validate required object attributes against Benchling schema metadata.

        Args:
            object_map: Object map describing attribute mappings.
            sample: STS sample data object being validated.
            validation_object: Validation result to update.
            benchling_schema: Benchling schema field metadata for the object type.
            benchling_object_type: Destination Benchling object type.

        Returns:
            bool: True when at least one attribute validation failed.
        """
        failed = self._populate_concatenated_attributes(
            sample,
            object_map,
            validation_object,
            benchling_object_type,
        )
        attribute_map = object_map.get('attribute_map', {})

        for benchling_key, sts_key in attribute_map.items():
            if self._is_computed_attribute(sts_key):
                continue

            if benchling_key in benchling_schema:
                failed = (
                    self._validate_schema_attribute(
                        object_map,
                        sample,
                        validation_object,
                        benchling_schema,
                        benchling_object_type,
                        benchling_key,
                        sts_key,
                    )
                    or failed
                )
            elif self._is_required_non_schema_attribute(benchling_key):
                failed = (
                    self._validate_required_non_schema_attribute(
                        object_map,
                        sample,
                        validation_object,
                        benchling_schema,
                        benchling_object_type,
                        benchling_key,
                        sts_key,
                    )
                    or failed
                )

        return failed

    def _validate_schema_attribute(
            self,
            object_map: dict[str, Any],
            sample: DataObject,
            validation_object: ValidateObject,
            benchling_schema: dict[str, Any],
            benchling_object_type: str,
            benchling_key: str,
            sts_key: str,
    ) -> bool:
        """Validate one mapped schema attribute for a sample.

        Args:
            object_map: Object map describing relationships and attribute mappings.
            sample: STS sample data object being validated.
            validation_object: Validation result to update.
            benchling_schema: Benchling schema field metadata for the object type.
            benchling_object_type: Destination Benchling object type.
            benchling_key: Benchling schema field key being validated.
            sts_key: STS attribute or relationship key supplying the value.

        Returns:
            bool: True when the attribute validation failed.
        """
        attribute = self._build_attribute(
            object_type=benchling_object_type,
            sts_identifier=sts_key,
            benchling_identifier=benchling_key,
        )
        required = benchling_schema[benchling_key].get('required', False)

        if sts_key in object_map.get('benchling_relationships', []):
            self._check_benchling_relationship_available(sample, sts_key, attribute)
        elif sts_key in object_map.get('benchling_multiselect_relationships', []):
            self._check_multiselect_benchling_relationships(
                sample,
                sts_key,
                attribute,
            )
        else:
            attribute['sts_value'] = (
                sample.id
                if sts_key == 'id'
                else sample.attributes.get(sts_key)
            )
            try:
                attribute['benchling_value'] = self._sanitize_attribute(
                    benchling_key,
                    attribute['sts_value'],
                    benchling_schema,
                )
            except Exception as exc:
                attribute['benchling_value'] = None
                attribute['passed'] = False
                attribute['failed_reason'] = f'Invalid value: {exc}'

        if attribute.get('passed') is not False:
            attribute['passed'] = True

        if required and self._is_missing(attribute.get('benchling_value')):
            attribute['passed'] = False
            attribute['failed_reason'] = 'Missing Required Value'

        self._add_attribute_from_dict(validation_object, attribute)
        return attribute.get('passed') is False

    def _validate_required_non_schema_attribute(
            self,
            object_map: dict[str, Any],
            sample: DataObject,
            validation_object: ValidateObject,
            benchling_schema: dict[str, Any],
            benchling_object_type: str,
            benchling_key: str,
            sts_key: str,
    ) -> bool:
        """Validate a required Benchling attribute that is not in the schema map.

        Args:
            object_map: Object map describing relationships and attribute mappings.
            sample: STS sample data object being validated.
            validation_object: Validation result to update.
            benchling_schema: Benchling schema metadata, if any is relevant.
            benchling_object_type: Destination Benchling object type.
            benchling_key: Benchling attribute key being validated.
            sts_key: STS attribute or relationship key supplying the value.

        Returns:
            bool: True when the attribute validation failed.
        """
        attribute = self._build_attribute(
            object_type=benchling_object_type,
            sts_identifier=self._display_sts_identifier(sts_key),
            benchling_identifier=benchling_key,
        )

        if sts_key in object_map.get('benchling_relationships', []):
            self._check_benchling_relationship_available(sample, sts_key, attribute)
        else:
            attribute['sts_value'] = (
                sample.id
                if sts_key == 'id'
                else sample.attributes.get(sts_key)
            )
            attribute['benchling_value'] = self._sanitize_attribute(
                benchling_key,
                attribute['sts_value'],
                benchling_schema,
            )
            attribute['passed'] = not self._is_missing(attribute['benchling_value'])
            if not attribute['passed']:
                attribute['failed_reason'] = 'Missing Required Value'

        self._add_attribute_from_dict(validation_object, attribute)
        return attribute.get('passed') is False

    def _populate_concatenated_attributes(
            self,
            sample: DataObject,
            object_map: dict[str, Any],
            validation_object: ValidateObject,
            benchling_object_type: str,
    ) -> bool:
        """Build and validate configured concatenated attributes for a sample.

        Args:
            sample: STS sample data object to inspect and mutate.
            object_map: Object map containing concatenated attribute configuration.
            validation_object: Validation result to update when values are missing.
            benchling_object_type: Destination Benchling object type.

        Returns:
            bool: True when a concatenated value could not be built.
        """
        failed = False

        for attribute_mapping in object_map.get('concatenated_values', []):
            if sample.attributes.get(attribute_mapping) is not None:
                continue

            concatenated_value = (
                StsSampleToCasmBenchlingConverterFactory
                .concatenated_value_for_sample(
                    self.mode,
                    sample,
                    attribute_mapping,
                )
            )
            values = {}
            for attribute in concatenated_value['values']:
                attribute_key, value = self._resolve_concatenated_attribute_value(
                    sample,
                    attribute,
                )
                values[attribute_key] = value

            missing_attributes = [
                attribute
                for attribute, value in values.items()
                if self._is_missing(value)
            ]
            if missing_attributes:
                failed = True
                self._add_attribute(
                    validation_object,
                    object_type=benchling_object_type,
                    sts_identifier=', '.join(missing_attributes),
                    benchling_identifier=attribute_mapping,
                    sts_value=None,
                    benchling_value=None,
                    passed=False,
                    failed_reason=(
                        f'Missing value(s) {missing_attributes} needed to build '
                        f'{attribute_mapping}'
                    ),
                )
                continue

            sample.attributes[attribute_mapping] = concatenated_value[
                'separator'
            ].join(str(value) for value in values.values())

        return failed

    def _resolve_concatenated_attribute_value(
            self,
            sample: DataObject,
            attribute: str | dict[str, str],
    ) -> tuple[str, Any]:
        """Resolve one source value used in a concatenated attribute.

        Args:
            sample: STS sample data object being inspected.
            attribute: Source attribute name or primary/fallback mapping.

        Returns:
            tuple[str, Any]: Display key and sanitized source value.
        """
        if isinstance(attribute, dict):
            primary_attribute = attribute['primary']
            fallback_attribute = attribute.get('fallback')

            value = sample.attributes.get(primary_attribute)
            selected_attribute = primary_attribute
            if self._is_missing(value):
                value = sample.attributes.get(fallback_attribute)
                selected_attribute = fallback_attribute

            attribute_key = f'{primary_attribute} or {fallback_attribute}'
            return attribute_key, self._sanitize_position_value(
                selected_attribute,
                value,
            )

        if attribute in self.BENCHLING_OBJECT_MAP[self.mode]:
            object_map = self._object_map_for_sample(attribute, sample)
            if object_map is None:
                return attribute, None
            value = self._get_object_primary_attribute_value(
                object_map,
                sample,
                attribute,
            )
            if not self._is_missing(value) and self._relationship_available(
                    object_type=attribute,
                    search_identifier=object_map['primary_attribute'],
                    search_value=value,
            ):
                return attribute, value
            return attribute, None

        if attribute in self.STS_OBJECT_MAP:
            sample.attributes[attribute] = (
                sample.attributes.get(attribute)
                or self._get_sts_relationship_attribute_value(attribute, sample)
            )

        value = sample.attributes.get(attribute)
        return attribute, self._sanitize_position_value(attribute, value)

    @staticmethod
    def _sanitize_position_value(attribute: str | None, value: Any) -> Any:
        """Normalize rack or well position values before validation.

        Args:
            attribute: Attribute name associated with the value.
            value: Raw source value.

        Returns:
            Any: Normalized position value, or the original value for other fields.
        """
        if attribute in ['pos_in_rack', 'TUBE_WELL_POSITION']:
            return re.sub(r'([A-Za-z]+)0', r'\1', str(value or ''))
        return value

    def _check_benchling_relationship_available(
            self,
            sample: DataObject,
            relationship_object_type: str,
            attribute: Attribute,
    ) -> None:
        """Validate that a single Benchling relationship value is available.

        Args:
            sample: STS sample data object being validated.
            relationship_object_type: Benchling object type required as a relationship.
            attribute: Mutable validation attribute to populate with the result.
        """
        try:
            relationship_object_map = self._object_map_for_sample(
                relationship_object_type,
                sample,
            )
        except ValueError as exc:
            attribute['sts_value'] = None
            attribute['benchling_value'] = None
            attribute['passed'] = False
            attribute['failed_reason'] = str(exc)
            return

        if relationship_object_map is None:
            attribute['sts_value'] = None
            attribute['benchling_value'] = None
            attribute['passed'] = False
            attribute['failed_reason'] = (
                f'Unsupported relationship type {relationship_object_type}'
            )
            return

        search_value = self._get_object_primary_attribute_value(
            relationship_object_map,
            sample,
            relationship_object_type,
        )

        if self._is_missing(search_value):
            attribute['sts_value'] = None
            attribute['benchling_value'] = None
            attribute['passed'] = False
            attribute['failed_reason'] = 'Missing Required Value for relationship lookup'
            return

        if self._relationship_available(
                object_type=relationship_object_type,
                search_identifier=relationship_object_map['primary_attribute'],
                search_value=search_value,
        ):
            attribute['sts_value'] = search_value
            attribute['benchling_value'] = search_value
            attribute['passed'] = True
            return

        attribute['sts_value'] = search_value
        attribute['benchling_value'] = None
        attribute['passed'] = False
        attribute['failed_reason'] = (
            'Missing Required relationship in Benchling or current import '
            f'for value: {search_value}'
        )

    def _check_multiselect_benchling_relationships(
            self,
            sample: DataObject,
            relationship_object_type: str,
            attribute: Attribute,
    ) -> None:
        """Validate configured multiselect Benchling relationship values.

        Args:
            sample: STS sample data object being validated.
            relationship_object_type: Benchling multiselect relationship type.
            attribute: Mutable validation attribute to populate with the result.
        """
        relationship_maps = self.MULTISELECT_BENCHLING_RELATIONSHIPS[
            self.mode
        ].get(relationship_object_type, {})

        sts_values = []
        benchling_values = []
        failures = []
        for relationship_object_map in relationship_maps.values():
            search_value = self._get_object_primary_attribute_value(
                relationship_object_map,
                sample,
                relationship_object_type,
            )
            if self._is_missing(search_value):
                continue

            sts_values.append(search_value)
            if self._relationship_available(
                    object_type=relationship_object_type,
                    search_identifier=relationship_object_map['primary_attribute'],
                    search_value=search_value,
                    secondary_search_identifier=relationship_object_map.get(
                        'secondary_attribute'
                    ),
                    secondary_search_value=relationship_object_map.get(
                        'secondary_attribute_value'
                    ),
            ):
                benchling_values.append(search_value)
            else:
                failures.append(search_value)

        attribute['sts_value'] = sts_values
        attribute['benchling_value'] = benchling_values
        if failures:
            attribute['passed'] = False
            attribute['failed_reason'] = (
                'Missing Required relationship in Benchling for value(s): '
                f'{failures}'
            )
        else:
            attribute['passed'] = True

    def _relationship_available(
            self,
            object_type: str,
            search_identifier: str,
            search_value: Any,
            secondary_search_identifier: str | None = None,
            secondary_search_value: str | None = None,
    ) -> bool:
        """Check whether a relationship target exists or is planned in this import.

        Args:
            object_type: Benchling object type to search.
            search_identifier: Primary Benchling search field.
            search_value: Primary search value.
            secondary_search_identifier: Optional secondary schema field.
            secondary_search_value: Optional secondary field value.

        Returns:
            bool: True when the relationship target is available.
        """
        if self._is_missing(search_value):
            return False

        search_value = str(search_value)
        if search_value in self._planned_values.get(object_type, set()):
            return True
        if search_value in self._stored_values.get(object_type, {}):
            return True

        benchling_value = self._get_benchling_object_value(
            object_type=object_type,
            search_identifier=search_identifier,
            search_value=search_value,
            secondary_search_identifier=secondary_search_identifier,
            secondary_search_value=secondary_search_value,
        )
        if benchling_value is None:
            return False

        self._stored_values.setdefault(object_type, {})[search_value] = benchling_value
        return True

    def _get_object_primary_attribute_value(
            self,
            object_map: dict[str, Any],
            sample: DataObject,
            object_map_key: str,
    ) -> Any:
        """Resolve and sanitize the primary attribute value for an object map.

        Args:
            object_map: Object map containing primary attribute metadata.
            sample: STS sample data object being validated.
            object_map_key: Benchling object type used for schema lookup.

        Returns:
            Any: Sanitized primary attribute value, or None when unavailable.
        """
        benchling_attribute_identifier = object_map.get('primary_attribute')
        if benchling_attribute_identifier is None:
            return None

        sts_attribute_identifier = object_map['attribute_map'][
            benchling_attribute_identifier
        ]

        if (
                sts_attribute_identifier in object_map.get('sts_relationships', [])
                and sts_attribute_identifier in self.STS_OBJECT_MAP
        ):
            self._populate_sts_relationships(sample, object_map)
        elif (
                sts_attribute_identifier in object_map.get('concatenated_values', [])
                and sample.attributes.get(sts_attribute_identifier) is None
        ):
            self._populate_concatenated_attributes(
                sample,
                object_map,
                ValidateObject(sample_id=str(sample.id)),
                object_map_key,
            )

        if sts_attribute_identifier in ['id', 'sts_id']:
            attribute_value = sample.id
        else:
            attribute_value = sample.attributes.get(sts_attribute_identifier)

        benchling_schema = self.get_benchling_schema(object_map_key)

        return self._sanitize_attribute(
            benchling_attribute_identifier,
            attribute_value,
            benchling_schema,
        )

    def get_benchling_schema(self, benchling_object_type: str) -> dict[str, Any]:
        """Return Benchling schema metadata for an object type.

        Args:
            benchling_object_type: Benchling object type to inspect.

        Returns:
            dict[str, Any]: Schema field metadata, or an empty dict for transfers.
        """
        if benchling_object_type == 'transfer':
            return {}

        object_type = self.benchling.benchling_types[benchling_object_type]
        return self.benchling.schemas[object_type][benchling_object_type]

    def _sanitize_attribute(
            self,
            key: str,
            value: Any,
            benchling_schema: dict[str, Any],
    ) -> Any:
        """Coerce and replace a value according to Benchling schema metadata.

        Args:
            key: Benchling schema field or attribute key.
            value: Raw value from STS or relationship resolution.
            benchling_schema: Benchling schema metadata for the object type.

        Returns:
            Any: Value coerced into the shape expected by Benchling.
        """
        fields = benchling_schema

        if fields and key in fields:
            if fields[key]['type'] == 'int':
                if value:
                    value = int(value)
                else:
                    value = 0

            if fields[key]['type'] == 'str' and not isinstance(
                    value,
                    (list, tuple, set),
            ):
                if value:
                    value = str(value)

                if key in self.VALUE_REPLACEMENTS[self.mode]:
                    if value in self.VALUE_REPLACEMENTS[self.mode][key]:
                        value = self.VALUE_REPLACEMENTS[self.mode][key][value]
                    elif 'default' in self.VALUE_REPLACEMENTS[self.mode][key]:
                        value = self.VALUE_REPLACEMENTS[self.mode][key]['default']

                if fields[key]['is_multi']:
                    value = [value]

            if fields[key]['is_multi'] and isinstance(value, (list, tuple, set)):
                sanitized_values = []
                for item in value:
                    if fields[key]['type'] == 'str':
                        sanitized_values.append(str(item))
                    elif fields[key]['type'] == 'int':
                        sanitized_values.append(int(item))
                    else:
                        sanitized_values.append(item)
                value = sanitized_values

            if key == 'genetically_modified':
                value = self.VALUE_REPLACEMENTS[self.mode][key]['default']

        return value

    def _get_benchling_object_value(
            self,
            object_type: str,
            search_identifier: str,
            search_value: str,
            secondary_search_identifier: str | None = None,
            secondary_search_value: str | None = None,
    ) -> str | None:
        """Look up a Benchling object id by primary and optional secondary filters.

        Args:
            object_type: Benchling object type to search.
            search_identifier: Primary field or attribute to filter on.
            search_value: Primary value to match.
            secondary_search_identifier: Optional secondary schema field.
            secondary_search_value: Optional secondary value to match.

        Returns:
            str | None: Benchling object id when found, otherwise None.

        Raises:
            Exception: If the configured Benchling object type cannot be searched.
            BenchlingError: If Benchling returns an error other than invalid barcodes.
        """
        filter_object = DataSourceFilter()
        is_barcode_lookup = False
        benchling_type = self.benchling.benchling_types[object_type]

        if benchling_type == 'custom_entity':
            schema_filter = DataSourceFilter()
            schema_filter.and_ = {
                search_identifier: {'eq': {'value': search_value}},
            }
            if secondary_search_identifier and secondary_search_value:
                schema_filter.and_[secondary_search_identifier] = {
                    'eq': {'value': secondary_search_value},
                }
            filter_object.and_ = {'schema_fields': schema_filter}
        elif benchling_type in ['box', 'plate', 'container', 'location']:
            if search_identifier == 'barcode':
                search_identifier = 'barcodes'
            is_barcode_lookup = search_identifier == 'barcodes'
            filter_object.and_ = {
                search_identifier: {'in_list': {'value': [search_value]}},
            }
        elif benchling_type in ['assay_result']:
            filter_object.and_ = {
                'entity_ids': {'in_list': {'value': [search_value]}},
            }
        else:
            raise Exception(
                f'Configuration error: Unsupported search of type {object_type}'
            )

        try:
            benchling_object = next(
                iter(self.benchling.get_list(object_type, filter_object))
            )

            if hasattr(benchling_object, 'id'):
                return benchling_object.id
        except BenchlingError as exc:
            if self._is_invalid_barcode_lookup_error(exc, is_barcode_lookup):
                return None
            raise
        except StopIteration:
            return None

        return None

    def _populate_polymorphic_benchling_relationships(
            self,
            sample: DataObject,
            object_map: dict[str, Any],
    ) -> None:
        """Resolve dynamic relationship aliases into concrete Benchling types.

        Args:
            sample: STS sample data object used for dynamic type detection.
            object_map: Object map to mutate with concrete relationship types.
        """
        for relationship in object_map.get('polymorphic_benchling_relationships', []):
            relationship_object_type = self._detect_destination_object_type(
                sample=sample,
                detect_destination_type=relationship,
            )

            if (
                    relationship_object_type
                    and relationship_object_type not in object_map['benchling_relationships']
            ):
                key_for_relationship_object_type = next(
                    (
                        key
                        for key, value in object_map['attribute_map'].items()
                        if relationship == value
                    ),
                    None,
                )

                if key_for_relationship_object_type:
                    object_map['benchling_relationships'].append(
                        relationship_object_type
                    )
                    object_map['attribute_map'][key_for_relationship_object_type] = (
                        relationship_object_type
                    )

    def _detect_destination_object_type(
            self,
            sample: DataObject,
            detect_destination_type: str,
    ) -> str | None:
        """Detect a concrete destination object type without raising validation errors.

        Args:
            sample: STS sample data object used for type detection.
            detect_destination_type: Dynamic destination alias to resolve.

        Returns:
            str | None: Concrete destination object type, or None when unsupported.
        """
        return (
            StsSampleToCasmBenchlingConverterFactory
            .destination_object_type_for_sample(
                self.mode,
                sample,
                detect_destination_type,
                raise_exception=False,
            )
        )

    @staticmethod
    def _is_invalid_barcode_lookup_error(
            exc: BenchlingError,
            is_barcode_lookup: bool,
    ) -> bool:
        """Check whether a Benchling error is an ignorable invalid-barcode lookup.

        Args:
            exc: Benchling SDK error raised during lookup.
            is_barcode_lookup: Whether the lookup used the barcode endpoint.

        Returns:
            bool: True when the error represents invalid barcode input.
        """
        if not is_barcode_lookup:
            return False
        if getattr(exc, 'status_code', None) != 400:
            return False

        message = getattr(exc, 'json', None) or getattr(exc, 'message', None)
        if not isinstance(message, dict):
            return False

        error = message.get('error', {})
        return isinstance(error, dict) and bool(error.get('invalidBarcodes'))

    def _build_attribute(
            self,
            *,
            object_type: str,
            sts_identifier: str,
            benchling_identifier: str,
    ) -> Attribute:
        """Build a validation attribute with display-ready identifiers.

        Args:
            object_type: Benchling object type being validated.
            sts_identifier: STS source identifier for the value.
            benchling_identifier: Benchling field or relationship identifier.

        Returns:
            Attribute: Initialized validation attribute marked as passing.
        """
        return {
            'object_type': object_type,
            'sts_identifier': self._display_sts_identifier(sts_identifier),
            'benchling_identifier': f'{object_type}.{benchling_identifier}',
            'passed': True,
        }

    def _add_attribute(
            self,
            validation_object: ValidateObject,
            *,
            object_type: str,
            sts_identifier: str,
            benchling_identifier: str,
            sts_value: Any,
            benchling_value: Any,
            passed: bool,
            failed_reason: str | None = None,
    ) -> None:
        """Add a fully populated validation attribute to a validation result.

        Args:
            validation_object: Validation result to update.
            object_type: Benchling object type being validated.
            sts_identifier: STS source identifier for the value.
            benchling_identifier: Benchling field or relationship identifier.
            sts_value: Raw or resolved STS value.
            benchling_value: Value expected or found in Benchling.
            passed: Whether the validation check passed.
            failed_reason: Optional reason for validation failure.
        """
        attribute = self._build_attribute(
            object_type=object_type,
            sts_identifier=sts_identifier,
            benchling_identifier=benchling_identifier,
        )
        attribute['sts_value'] = sts_value
        attribute['benchling_value'] = benchling_value
        attribute['passed'] = passed
        if failed_reason:
            attribute['failed_reason'] = failed_reason

        self._add_attribute_from_dict(validation_object, attribute)

    def _add_attribute_from_dict(
            self,
            validation_object: ValidateObject,
            attribute: Attribute,
    ) -> None:
        """Add a validation attribute dictionary while preserving duplicate keys.

        Args:
            validation_object: Validation result to update.
            attribute: Validation attribute dictionary to add.
        """
        key = attribute['benchling_identifier']
        if key in validation_object.attributes:
            key = f'{key}#{len(validation_object.attributes)}'
        validation_object.attributes[key] = attribute

    @staticmethod
    def _display_sts_identifier(sts_identifier: str) -> str:
        """Return a human-readable label for selected STS identifiers.

        Args:
            sts_identifier: Raw STS attribute or computed identifier.

        Returns:
            str: Display label for validation output.
        """
        if sts_identifier == 'box_and_position':
            return 'Rack/box and position'
        if sts_identifier == 'plate_and_location':
            return 'Plate and well position'
        if sts_identifier == 'plate_and_location_non_relationship':
            return 'Plate ID: Well Position'
        if sts_identifier == 'storage_rack':
            return 'Rack/Plate ID'
        return sts_identifier

    def _is_computed_attribute(self, attr_mapping: str) -> bool:
        """Check whether an attribute mapping is computed by the converter.

        Args:
            attr_mapping: STS attribute mapping identifier.

        Returns:
            bool: True when the mapping is configured as computed.
        """
        return attr_mapping in self.COMPUTED_VALUES[self.mode]

    @staticmethod
    def _is_required_non_schema_attribute(benchling_key: str) -> bool:
        """Check whether a non-schema Benchling attribute is required.

        Args:
            benchling_key: Benchling attribute key.

        Returns:
            bool: True for required non-schema Benchling attributes.
        """
        return benchling_key in {
            'barcode',
            'parent_storage_id',
            'source_entity_id',
            'destination_container_id',
        }

    @staticmethod
    def _is_missing(value: Any) -> bool:
        """Return whether a value should be treated as missing.

        Args:
            value: Value to inspect.

        Returns:
            bool: True for None, empty strings, and empty lists.
        """
        return value is None or value == '' or value == []
