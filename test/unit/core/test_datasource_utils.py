# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Any, Iterable, Optional
from unittest.mock import MagicMock

import pytest

from tol.core import (
    DataObject,
    DataSource,
    DataSourceError,
    DataSourceFilter,
    DataSourceUtils,
    core_data_object
)
from tol.core.operator import (
    DetailGetter,
    GroupStatter,
    ListGetter,
    Relational
)
from tol.core.operator.provenancer import ProvenanceField
from tol.core.relationship import RelationshipConfig


@pytest.fixture
def mock_config_datasource() -> DataSource:
    class _MockConfigDataSource(DataSource):
        @property
        def supported_types(self) -> list[str]:
            return ['data_source_instance']

        @property
        def attribute_types(self) -> dict[str, str]:
            return {
                'data_source_instance': {}
            }

        def get_one(
            self,
            object_type: str,
            object_id: str
        ) -> Optional[DataObject]:
            return self.data_object_factory(
                type_=object_type,
                id_=object_id,
                attributes={
                    'builtin_name': 'portal'
                }
            )

    mock_ds = _MockConfigDataSource(config={})
    core_data_object(mock_ds)
    return mock_ds


@pytest.fixture
def mock_datasource() -> DataSource:
    class _MockDataSource(
        DataSource, DetailGetter, GroupStatter, ListGetter, Relational
    ):
        raise_error: bool = False

        @property
        def supported_types(self) -> list[str]:
            return ['parent', 'child']

        @property
        def attribute_types(self) -> dict[str, str]:
            return {
                'parent': {},
                'child': {
                    'sortable_attribute': 'string'
                }
            }

        @property
        def relationship_config(self) -> dict[str, RelationshipConfig]:
            return {
                'child': RelationshipConfig(to_one={'parent': 'parent'})
            }

        def get_to_one_relation(self, source, relationship_name, session=None):
            child_id = source.id[-1]
            parent_id = (int(child_id) % 2) + 1
            return self.data_object_factory(
                'parent',
                id_=f'parent{parent_id}'
            )

        def get_to_many_relations(self, source, relationship_name, session=None):
            raise NotImplementedError()

        def get_by_id(
            self,
            object_type: str,
            object_ids: Iterable[str],
            requested_fields: list[str] = None,
        ) -> Iterable[Optional[DataObject]]:
            for c in range(2):
                yield self.data_object_factory(
                    type_=object_type,
                    id_=f'child{c}',
                    attributes={
                        'sortable_attribute': f'{100-c}',
                    }
                )

        def get_list(
            self,
            object_type: str,
            object_filters: DataSourceFilter = None
        ) -> Iterable[Optional[DataObject]]:
            for c in range(4):
                yield self.data_object_factory(
                    type_=object_type,
                    id_=f'child{c}',
                    attributes={
                        'sortable_attribute': f'{100-c}',
                    }
                )

        def get_group_stats(
            self,
            object_type: str,
            group_by: list[str],
            stats_fields: list[str] = [],
            stats: list[str] = ['min', 'max'],
            object_filters: Optional[DataSourceFilter] = None
        ) -> Iterable[dict[Any, int]]:
            if self.raise_error:
                raise DataSourceError('Group stats not supported')
            mock_objects = [
                {
                    'key': {'parent.id': 'parent1'},
                    'stats': {
                        'count': 3,
                    }
                }, {
                    'key': {'parent.id': 'parent2'},
                    'stats': {
                        'count': 17,
                    }
                }
            ]
            for obj in mock_objects:
                yield obj

    mock_ds = _MockDataSource(config={})
    core_data_object(mock_ds)

    return mock_ds


class TestUtils:

    def test_get_datasource_by_name(
        self
    ) -> None:

        ds = DataSourceUtils.get_datasource_by_name(
            name='portal',
            environment='test'
        )
        assert isinstance(ds, DataSource)

    def test_get_ids(
            self,
            mock_datasource: DataSource
    ):
        ids = list(DataSourceUtils.get_ids(
            datasource=mock_datasource,
            object_type='child',
            id_attribute='parent.id'
        ))
        assert ids == ['parent1', 'parent2']

    def test_get_ids_fallback(
            self,
            mock_datasource: DataSource
    ):
        mock_datasource.raise_error = True

        ids = DataSourceUtils.get_ids(
            datasource=mock_datasource,
            object_type='child',
            id_attribute='parent.id'
        )

        assert list(ids) == ['parent1', 'parent2']

    def test_get_objects_from_ids(
            self,
            mock_datasource: DataSource
    ):
        objects = list(DataSourceUtils.get_objects_from_ids(
            datasource=mock_datasource,
            object_type='child',
            ids=['child0', 'child1'],
            sort_by='sortable_attribute'
        ))

        assert len(objects) == 2
        assert objects[0].id == 'child0'
        assert objects[1].id == 'child1'

    def test_get_datasource(
            self,
            mock_config_datasource: DataSource
    ):
        ds = DataSourceUtils.get_datasource(
            datasource_instance_id='tol_production',
            config_datasource=mock_config_datasource
        )
        assert isinstance(ds, DataSource)

    def test_get_provenance_fields_skips_none_source_order(self):
        rel = MagicMock()
        rel.source_order = None
        config = MagicMock()
        config.data_source_config_relationships = [rel]

        result = DataSourceUtils.get_provenance_fields([], [rel])

        assert result == {}

    def test_get_provenance_fields_with_source_order(self):
        att = MagicMock()
        att.source_order = ['source1', 'source2']
        att.return_type = 'int'
        att.object_type = 'sample'
        att.name = 'att_name'
        rel = MagicMock()
        rel.source_order = ['source1', 'source2']
        rel.object_type = 'sample'
        rel.name = 'rel_name'
        rel.return_type = None

        result = DataSourceUtils.get_provenance_fields([att], [rel])
        assert result == {
            'sample': {
                'att_name': ProvenanceField(
                    source_order=['source1', 'source2'],
                    return_type='int'
                ),
                'rel_name': ProvenanceField(
                    source_order=['source1', 'source2'],
                    return_type='str'
                )
            }}
