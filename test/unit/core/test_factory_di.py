# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock

import pytest

from tol.core import DataObject, DataSource, core_data_object
from tol.core.factory import CoreDataObject, _data_source_registry
from tol.core.operator import DetailGetter, Relational
from tol.core.relationship import RelationshipConfig


class _MockDataSource(DataSource):
    @property
    def supported_types(self):
        return ['test_type']

    @property
    def attribute_types(self):
        return {'test_type': {'name': 'str'}}


class _RelDS(DataSource, Relational):
    @property
    def supported_types(self):
        return ['rel_type']

    @property
    def attribute_types(self):
        return {'rel_type': {'name': 'str'}}

    @property
    def relationship_config(self):
        return {
            'rel_type': RelationshipConfig(
                to_one={'parent': 'rel_type'},
            )
        }


class TestCoreDataObjectDI:
    def test_isinstance_across_sources(self):
        """Objects from different core_data_object calls share the same type."""
        ds1 = _MockDataSource({})
        ds2 = _RelDS({})
        core_data_object(ds1)
        core_data_object(ds2)

        obj1 = CoreDataObject('test_type', id_='1')
        obj2 = CoreDataObject('rel_type', id_='2')
        assert isinstance(obj1, CoreDataObject)
        assert isinstance(obj2, CoreDataObject)
        assert type(obj1) is type(obj2)

    def test_registry_contains_registered_types(self):
        """Registered DataSource types appear in the registry."""
        ds = _MockDataSource({})
        core_data_object(ds)
        assert 'test_type' in _data_source_registry
        assert _data_source_registry['test_type'] is ds

    def test_registry_additive(self):
        """Multiple core_data_object calls accumulate types."""
        ds1 = _MockDataSource({})
        ds2 = _RelDS({})
        core_data_object(ds1)
        core_data_object(ds2)
        assert 'test_type' in _data_source_registry
        assert 'rel_type' in _data_source_registry

    def test_importable_type(self):
        """CoreDataObject can be imported and used as a type."""
        ds = _MockDataSource({})
        core_data_object(ds)
        obj = CoreDataObject('test_type', id_='1')

        assert isinstance(obj, DataObject)
        assert isinstance(obj, CoreDataObject)

    def test_host_resolved_from_registry(self):
        """_host property reads from the module-level registry."""
        ds = _RelDS({})
        core_data_object(ds)
        obj = CoreDataObject('rel_type', id_='1')
        assert obj._host is ds

    def test_core_data_object_returns_class(self):
        """core_data_object returns the CoreDataObject class itself."""
        ds = _MockDataSource({})
        result = core_data_object(ds)
        assert result is CoreDataObject

    def test_factory_injected_into_datasource(self):
        """core_data_object injects a callable factory into DataSource."""
        ds = _MockDataSource({})
        core_data_object(ds)
        assert ds.data_object_factory is not None
        obj = ds.data_object_factory('test_type', id_='x')
        assert isinstance(obj, CoreDataObject)
        assert obj.id == 'x'


class TestRegistryCleanup:
    """Verifies the autouse fixture isolates tests."""

    def test_direct_registry_injection(self):
        """DataSources can be injected into the registry directly for testing."""
        mock_ds = Mock()
        _data_source_registry['injected_type'] = mock_ds
        assert _data_source_registry['injected_type'] is mock_ds

    def test_registry_empty_after_cleanup(self):
        """
        This test runs after test_direct_registry_injection.
        The fixture should have cleaned up 'injected_type'.
        """
        assert 'injected_type' not in _data_source_registry
