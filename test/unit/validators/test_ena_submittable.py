# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterable
from unittest.mock import create_autospec

from tol.core import DataObject, DataSource, core_data_object
from tol.core.operator import DetailGetter
from tol.validators import EnaSubmittableValidator


class _MockDataSource(DataSource, DetailGetter):

    def __init__(self, config: dict[str, Any]):
        super().__init__(config, [])

    def get_by_id(self):
        pass

    def get_one(self, object_type: str, object_id, **kwargs):
        del object_type, kwargs

        if object_id == 'a':
            return None
        elif object_id == 'b':
            return self.data_object_factory(
                'submittable_taxon',
                object_id,
                attributes={
                    'binomial': True,
                    'submittable': True,
                    'rank': 'species',
                }
            )
        elif object_id == 'c':
            return self.data_object_factory(
                'submittable_taxon',
                object_id,
                attributes={
                    'binomial': True,
                    'submittable': False,
                    'rank': 'species',
                }
            )
        elif object_id == 'd':
            return self.data_object_factory(
                'submittable_taxon',
                object_id,
                attributes={
                    'binomial': False,
                    'submittable': True,
                    'rank': 'species',
                }
            )
        elif object_id == 'e':
            return self.data_object_factory(
                'submittable_taxon',
                object_id,
                attributes={
                    'binomial': True,
                    'submittable': True,
                    'rank': 'subspecies',
                }
            )
        elif object_id == 'f':
            return self.data_object_factory(
                'submittable_taxon',
                object_id,
                attributes={
                    'binomial': True,
                    'submittable': True,
                    'rank': 'genus',
                }
            )
        elif object_id == '32644':
            return self.data_object_factory(
                'submittable_taxon',
                object_id,
                attributes={
                    'binomial': False,
                    'submittable': True,
                    'rank': 'species',
                }
            )

        return None

    @property
    def supported_types(self) -> list[str]:
        return ['submittable_taxon']


class TestEnaSubmittableValidator:

    def _make_mock_obj(self, taxon_id: str) -> DataObject:
        obj: DataObject = create_autospec(DataObject)
        obj.id = taxon_id
        obj.attributes = {
            'key1': taxon_id,
        }
        obj.get_field_by_name.side_effect = lambda field_name: obj.attributes.get(field_name)
        return obj

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

    def test_not_found_in_ena(self) -> None:
        mock_ds = _MockDataSource({})
        core_data_object(mock_ds)

        validator = EnaSubmittableValidator(
            config=EnaSubmittableValidator.Config(field_name='key1'),
            ena_datasource=mock_ds,
        )

        obj = self._make_mock_obj('a')

        list(validator.validate([obj]))

        assert validator.results
        assert len(validator.errors) == 1
        assert len(validator.warnings) == 0

    def test_valid_species_passes(self) -> None:
        mock_ds = _MockDataSource({})
        core_data_object(mock_ds)

        validator = EnaSubmittableValidator(
            config=EnaSubmittableValidator.Config(field_name='key1'),
            ena_datasource=mock_ds,
        )

        obj = self._make_mock_obj('b')

        list(validator.validate([obj]))

        assert len(validator.errors) == 0
        assert len(validator.warnings) == 0

    def test_not_submittable_gives_error(self) -> None:
        mock_ds = _MockDataSource({})
        core_data_object(mock_ds)

        validator = EnaSubmittableValidator(
            config=EnaSubmittableValidator.Config(field_name='key1'),
            ena_datasource=mock_ds,
        )

        obj = self._make_mock_obj('c')

        list(validator.validate([obj]))

        assert validator.results
        assert len(validator.errors) == 1
        assert len(validator.warnings) == 0

    def test_not_binomial_gives_error(self) -> None:
        mock_ds = _MockDataSource({})
        core_data_object(mock_ds)

        validator = EnaSubmittableValidator(
            config=EnaSubmittableValidator.Config(field_name='key1'),
            ena_datasource=mock_ds,
        )

        obj = self._make_mock_obj('d')

        list(validator.validate([obj]))

        assert validator.results
        assert len(validator.errors) == 1
        assert len(validator.warnings) == 0

    def test_subspecies_gives_warning(self) -> None:
        mock_ds = _MockDataSource({})
        core_data_object(mock_ds)

        validator = EnaSubmittableValidator(
            config=EnaSubmittableValidator.Config(field_name='key1'),
            ena_datasource=mock_ds,
        )

        obj = self._make_mock_obj('e')

        list(validator.validate([obj]))

        assert validator.results
        assert len(validator.errors) == 0
        assert len(validator.warnings) == 1

    def test_invalid_rank_gives_error(self) -> None:
        mock_ds = _MockDataSource({})
        core_data_object(mock_ds)

        validator = EnaSubmittableValidator(
            config=EnaSubmittableValidator.Config(field_name='key1'),
            ena_datasource=mock_ds,
        )

        obj = self._make_mock_obj('f')

        list(validator.validate([obj]))

        assert validator.results
        assert len(validator.errors) == 1
        assert len(validator.warnings) == 0

    def test_32644_exception_passes(self) -> None:
        mock_ds = _MockDataSource({})
        core_data_object(mock_ds)

        validator = EnaSubmittableValidator(
            config=EnaSubmittableValidator.Config(field_name='key1'),
            ena_datasource=mock_ds,
        )

        obj = self._make_mock_obj('32644')

        list(validator.validate([obj]))

        assert len(validator.errors) == 0
        assert len(validator.warnings) == 0

    def test_mixed_results(self) -> None:
        mock_ds = _MockDataSource({})
        core_data_object(mock_ds)

        validator = EnaSubmittableValidator(
            config=EnaSubmittableValidator.Config(field_name='key1'),
            ena_datasource=mock_ds,
        )

        objs = [
            self._make_mock_obj('a'),
            self._make_mock_obj('b'),
            self._make_mock_obj('c'),
            self._make_mock_obj('d'),
            self._make_mock_obj('e'),
            self._make_mock_obj('f'),
            self._make_mock_obj('32644'),
        ]

        list(validator.validate(objs))

        assert validator.results
        assert len(validator.errors) == 4
        assert len(validator.warnings) == 1
