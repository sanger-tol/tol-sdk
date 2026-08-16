# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import (
    OperableDataSource,
)
from tol.core.operator.provenancer import ProvenanceField

from ..dec import against
from ..fixtures import api_elastic, elastic


class TestAttributeTypes:
    """
    Tests an end-to-end interaction on each given `DataSource`
    instance.
    """

    @against(elastic, api_elastic)
    def test_attribute_types(self, data_source: OperableDataSource, ds_sleep):
        """
        Tests that the attribute types are correctly reported for each object type.
        """

        expected = {
            'root': {
                'str_column': 'str',
                'int_column': 'int',
                'datetime_column': 'datetime',
                'bool_column': 'bool',
                'list_column': 'str',
                'runtime_column': 'bool',
                'str_column_prov': 'str',
                'int_column_prov': 'int',
                'datetime_column_prov': 'datetime',
                'bool_column_prov': 'bool',
            },
            'related': {
                'str_column': 'str',
                'int_column': 'int',
                'datetime_column': 'datetime',
                'bool_column': 'bool',
                'list_column': 'str',
                'root_int_column_min': 'float',
                'root_int_column_max': 'float',
                'root_str_column_min': 'str',
                'root_str_column_max': 'str',
                'root_datetime_column_min': 'datetime',
                'root_datetime_column_max': 'datetime',
                'root_int_column_prov_max': 'int',
                'root_int_column_prov_min': 'int',
                'root_str_column_prov_max': 'str',
                'root_str_column_prov_min': 'str',
                'root_datetime_column_prov_max': 'datetime',
                'root_datetime_column_prov_min': 'datetime',
            }
        }
        assert data_source.attribute_types == expected

    @against(elastic, api_elastic)
    def test_supported_types(self, data_source: OperableDataSource, ds_sleep):
        """
        Tests that the supported types are correctly reported for each object type.
        """

        expected = {'root', 'related'}
        assert set(data_source.supported_types) == expected

    @against(elastic)
    def test_provenance_fields(self, data_source: OperableDataSource, ds_sleep):
        """
        Tests that the provenance fields are correctly reported for each object type.
        """

        expected = {
            'root': {
                'related_object.id': ProvenanceField(
                    source_order=['source1', 'source2', 'source3', 'source4'],
                    return_type=None
                ),
                'int_column_prov': ProvenanceField(
                    source_order=['source1', 'source2', 'source3', 'source4'],
                    return_type=None
                ),
                'str_column_prov': ProvenanceField(
                    source_order=['source1', 'source2', 'source3', 'source4'],
                    return_type=None
                ),
                'datetime_column_prov': ProvenanceField(
                    source_order=['source1', 'source2', 'source3', 'source4'],
                    return_type=None
                ),
                'bool_column_prov': ProvenanceField(
                    source_order=['source1', 'source2', 'source3', 'source4'],
                    return_type=None
                ),
            },
        }
        assert data_source.provenance_fields == expected
