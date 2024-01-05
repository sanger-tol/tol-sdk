# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from tol.core import OperableDataSource

from ..dec import against
from ..fixtures import all_fixtures


class TestEndToEnd:
    """
    Tests an end-to-end interaction on each given `DataSource`
    instance.
    """

    @against(*all_fixtures)
    def test_upsert_and_detail_get(self, data_source: OperableDataSource):
        """
        Upsert 3 `DataObject` instances, and get them by their IDs
        """

        ids = ['hype', 'train', 'max']

        # none of them are present yet
        first = list(
            data_source.get_by_id('root', ids)
        )

        assert first == [None, None, None]

        data_objects = [
            data_source.data_object_factory(
                'root',
                id_,
                attributes={'str_column': f'test_{id_}'}
            )
            for id_ in ids
        ]

        data_source.upsert('root', data_objects)

        # they should all be present now
        second = list(
            data_source.get_by_id('root', ids)
        )

        assert len(second) == 3

        for id_, obj in zip(ids, second):
            assert obj.id == id_
            assert obj.str_column == f'test_{id_}'
