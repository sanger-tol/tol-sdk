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
            },
            'related': {
                'str_column': 'str',
                'int_column': 'int',
                'datetime_column': 'datetime',
                'bool_column': 'bool',
                'list_column': 'str',
                'root_int_column_min': 'double',
                'root_int_column_max': 'double',
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
                'str_column': ProvenanceField(
                    source_order=['source1', 'source2', 'source3', 'source4'],
                    return_type='keyword'
                ),
            },
        }
        assert data_source.provenance_fields == expected
