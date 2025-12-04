# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any
from unittest.mock import PropertyMock, create_autospec

from pytest import fixture

from tol.core import DataObject, DataSource, DataSourceFilter
from tol.core.operator import DetailGetter
from tol.validators import TolidValidator


class _MockDataSource(DataSource, DetailGetter):

    def __init__(self, config: dict[str, Any]):
        super().__init__(config, [])

    def get_by_id(self):
        pass

    def get_one(self, object_type: str, object_id, **kwargs):
        mock_object = create_autospec(DataObject, instance=True)
        if object_id == 'FAIL':
            return None
        else:
            return_value = {'TAXON_ID': object_id}
            type(mock_object).attributes = PropertyMock(
                return_value=return_value
            )
            mock_object.get_field_by_name.return_value = object_id

            return [
                mock_object
            ]

    def get_list(self, object_type: str, filters: list[DataSourceFilter] = [], **kwargs):
        value = filters.and_['specimen_id']['eq']['value']
        if value == 'FAIL':
            mock_object = create_autospec(DataObject, instance=True)
            type(mock_object).attributes = PropertyMock(
                return_value={'SPECIMEN_ID': 'SPEC' + value}
            )
            # Create a mock species object with an id attribute that does not match
            # Taxon id in the original object
            mock_species = create_autospec(DataObject, instance=True)
            mock_species.id = 'SPECIESID_NOT_MATCH'
            type(mock_object).species = PropertyMock(
                return_value=mock_species
            )
            return [
                mock_object
            ]
        else:
            mock_object = create_autospec(DataObject, instance=True)
            type(mock_object).attributes = PropertyMock(
                return_value={'SPECIMEN_ID': 'SPEC' + value}
            )
            mock_species = create_autospec(DataObject, instance=True)
            mock_species.id = value.replace('SPEC', '')
            type(mock_object).species = PropertyMock(
                return_value=mock_species
            )
            return [
                mock_object
            ]

    @property
    def supported_types(self) -> list[str]:
        return ['species']


class TestTolidValidator:

    def test_warning_and_error(
        self,
        data_objects
    ) -> None:

        mock_datasource = _MockDataSource(config={})

        test_config = TolidValidator.Config(
            species_id_field='TAXON_ID',
            specimen_id_field='SPECIMEN_ID',
            error_ignore_field='IGNORE_FIELD',
            error_ignore_value='IGNORE_VALUE',
            warning_detail='TEST WARNING'
        )

        validator = TolidValidator(
            config=test_config,
            datasource=mock_datasource,
        )

        list(
            validator.validate(data_objects)
        )

        assert validator.results
        assert len(validator.errors) == 1
        assert len(validator.warnings) == 1

    def __make_side_effect(self, object_id):
        # Helper to create side effect function for get_field_by_name
        # name is the value passed to get_field_by_name
        def side_effect(name):
            values = {
                'TAXON_ID': object_id,
                'SPECIMEN_ID': f'SPEC{object_id}'
            }
            if object_id == 'FAIL':
                values = {
                    'TAXON_ID': 'FAIL',
                    'SPECIMEN_ID': 'FAIL'
                }
            return values.get(name)
        return side_effect

    @fixture
    def data_objects(
        self,
    ) -> list[DataObject]:
        mock_object = create_autospec(DataObject, instance=True)
        type(mock_object).attributes = PropertyMock(
            return_value={'TAXON_ID': 'ABC', 'SPECIMEN_ID': 'SPECABC'}
        )
        mock_object.get_field_by_name.side_effect = self.__make_side_effect('ABC')

        mock_object2 = create_autospec(DataObject, instance=True)
        type(mock_object2).attributes = PropertyMock(
            return_value={'TAXON_ID': 'DEF', 'SPECIMEN_ID': 'SPECDEF'}
        )
        mock_object2.get_field_by_name.side_effect = self.__make_side_effect('DEF')

        mock_object3 = create_autospec(DataObject, instance=True)
        type(mock_object3).attributes = PropertyMock(
            return_value={'TAXON_ID': 'FAIL', 'SPECIMEN_ID': 'SPECFAIL'}
        )
        mock_object3.get_field_by_name.side_effect = self.__make_side_effect('FAIL')

        return [
            mock_object,
            mock_object2,
            mock_object3
        ]
