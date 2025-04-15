# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict, Iterable

from tol.core import (
    DataSource,
    core_data_object
)
from tol.core.operator import DetailGetter


class _MockDataSource(DataSource, DetailGetter):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.call_count = 0

    def get_by_id(self, object_type: str, object_ids: Iterable[str], **kwargs):
        self.call_count += 1
        for object_id in object_ids:
            if int(object_id) <= 100:
                yield self.data_object_factory(
                    type_=object_type,
                    id_=object_id,
                    attributes={
                        'test_attribute': f'test_{object_id}'
                    }
                )
            else:
                yield None

    @property
    def attribute_types(self):
        return {
            'test': {
                'test_attribute': 'str'
            }
        }

    @property
    def supported_types(self):
        return ['test']


class TestDetailGetter:

    def test_to_one(self):
        mds = _MockDataSource({})
        core_data_object(mds)
        ret = mds.get_one('test', '1')
        assert ret.test_attribute == 'test_1'

        ret = mds.get_one('test', 200)
        assert ret is None

    def test_get_by_ids(self):
        mds = _MockDataSource({})
        core_data_object(mds)
        ret = list(mds.get_by_ids('test', map(str, range(50, 160))))
        assert mds.call_count == 6
        assert len(ret) == 110

        mds.call_count = 0
        mds.page_size = 50
        ret = list(mds.get_by_ids('test', map(str, range(50, 160))))
        assert mds.call_count == 3
        assert len(ret) == 110
