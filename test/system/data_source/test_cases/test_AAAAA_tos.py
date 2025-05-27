# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pathlib

from tol.core import (
    DataSourceFilter,
    DefaultDataLoader,
    OperableDataSource,
)
from tol.treeofsex import TOSConverter
from tol.treeofsex.excel import TOSEmitter

from ..dec import against
from ..fixtures import api_elastic, elastic


BASE_DIR = pathlib.Path(__file__).parent.resolve()


class TestTreeOfSex:
    """
    Tests a simple pipeline for Tree-of-Sex.
    """

    @against(elastic, api_elastic)
    def test_pipeline(
        self,
        data_source: OperableDataSource,
        ds_sleep
    ) -> None:

        filepath = BASE_DIR / 'objects.xlsx'
        yaml_path = BASE_DIR / 'tos.yaml'
        source_object_type = 'anything'

        emitter = TOSEmitter(
            filepath,
            'Sheet1',
            object_type=source_object_type
        )

        converter = TOSConverter(
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
        import logging; logging.error(list(
            d.id for d in data_source.get_list(
                'root',
                object_filters=f,
            )
        ))
        obj1, obj2 = list(
            data_source.get_list(
                'root',
                object_filters=f,
            )
        )

        assert obj1.id == '1'
        assert obj1.int_column == 42
        assert obj1.str_column == 'hello'

        assert obj2.id == '2'
        assert obj2.int_column == 9093
        assert obj2.str_column == 'world'
