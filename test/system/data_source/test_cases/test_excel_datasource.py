# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pathlib

from tol.converter import YamlConverter
from tol.core import (
    DataSourceFilter,
    DefaultDataLoader,
    OperableDataSource,
)
from tol.excel import ExcelDataSource

from ..dec import against
from ..fixtures import all_fixtures


BASE_DIR = pathlib.Path(__file__).parent.resolve()


class TestTreeOfSex:
    """
    Tests a simple pipeline for Tree-of-Sex.
    """

    @against(*all_fixtures)
    def test_pipeline(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ) -> None:

        filepath = BASE_DIR / 'objects.xlsx'
        yaml_path = BASE_DIR / 'tos.yaml'
        source_object_type = 'anything'

        emitter = ExcelDataSource(
            filepath,
            'Sheet1',
            object_type=source_object_type
        )

        converter = YamlConverter(
            data_source.data_object_factory,
            yaml_path,
            destination_object_type='root',
        )

        loader = DefaultDataLoader(
            emitter,
            data_source,
            [],
            source_object_type,
            'loader_mine_tos',
            destination_object_type='root',
            converter=converter,
        )

        loader.load(field_prefix='')

        ds_sleep(5)

        # exclude the archetype
        f = DataSourceFilter(
            and_={
                'str_column': {
                    'eq': {
                        'value': 'abc',
                        'negate': True,
                    }
                }
            }
        )
        obj1, obj2 = list(
            data_source.get_list(
                'root',
                object_filters=f,
            )
        )

        assert obj1.id == '2'
        assert obj1.int_column is None
        assert obj1.str_column == 'X:-:map_TO'

        assert obj2.id == '3'
        assert int(obj2.int_column) == 42
        assert obj2.str_column == 'Y'
