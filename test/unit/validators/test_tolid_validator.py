# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any

from tol.core import DataObject, DataSource
from tol.core.operator import DetailGetter
from unittest.mock import MagicMock, PropertyMock
from tol.validators import TolidValidator

class _MockDataSource(DataSource, DetailGetter):

    def __init__(self, config: dict[str, Any], ctx_getter=None):
        self.__ctx_getter = ctx_getter
        super().__init__(config, [])
        
    def get_by_id(self, object_type,):
        pass

    def get_one(self, object_type: str, object_id, **kwargs):
        mock_object = MagicMock()
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
    
    def get_list(
        self,
        object_type: str,
        filters: dict[str, Any] | None = None,
        **kwargs
    ) -> list[DataObject]:

        mock_object = MagicMock(DataObject)
        type(mock_object).attributes = PropertyMock(
            return_value={'TAXON_ID': 'ABC123'}
        )
        mock_object.get_field_by_name.return_value = 'ABC123'
        
        mock_object2 = MagicMock(DataObject)
        type(mock_object2).attributes = PropertyMock(
            return_value={'TAXON_ID': 'DEF123'}
        )
        mock_object2.get_field_by_name.return_value = 'DEF123'
        
        mock_object3 = MagicMock(DataObject)
        type(mock_object3).attributes = PropertyMock(
            return_value={'TAXON_ID': 'FAIL'}
        )
        mock_object3.get_field_by_name.return_value = 'FAIL'
        
        return [
            mock_object,
            mock_object2,
            mock_object3
        ]
    
    @property
    def supported_types(self) -> list[str]:
        return ['species']

class TestTolidValidator:

    def test_warning(
        self,
    ) -> None:
        
        mock_datasource = _MockDataSource(config={})
        mock_objs = mock_datasource.get_list(object_type='species')

        validator = TolidValidator(
            species_attribute='TAXON_ID',
            datasource=mock_datasource,
            warning_detail='TEST WARNING'
        )

        # consume the `Iterable`
        list (
            validator.validate(mock_objs)
        )

        assert validator.results
        assert len(validator.warnings) == 1