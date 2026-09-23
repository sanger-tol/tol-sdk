# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import pytest

from tol.core import (
    DataSourceFilter
)
from tol.sources.quasar import (
    quasar
)


class TestQuasarDataSource:

    def test_supported_types(self):
        qds = quasar()
        assert 'data_source_instance' in qds.supported_types
        assert 'data_source_config' in qds.supported_types
        assert 'data_source_config_attribute' in qds.supported_types
        assert 'data_source_config_relationship' in qds.supported_types
        assert 'data_source_config_summary' in qds.supported_types
        assert 'loader' in qds.supported_types
        assert 'loader_instance' in qds.supported_types

    def test_attribute_types(self):
        qds = quasar()

        assert 'data_source_instance' in qds.attribute_types
        assert qds.attribute_types['data_source_instance']['api_name'] == 'str'

    def test_relationship_config(self):
        qds = quasar()

        assert 'loader_instance' in qds.relationship_config
        assert qds.relationship_config['loader_instance'].to_one['loader'] == 'loader'

    def test_get_by_id(self):
        qds = quasar()

        ret = qds.get_by_ids('data_source_instance', ['test'])
        obj1 = next(ret)
        assert 'test' == obj1.id

        # Just pick out a few attributes here to test
        assert obj1.direct_name == 'elastic'
        assert obj1.api_name == 'portal'
        assert obj1.publish
        with pytest.raises(StopIteration):
            next(ret)

    def test_get_list(self):
        qds = quasar()

        f = DataSourceFilter()
        f.and_ = {
            'direct_name': {'eq': {'value': 'elastic'}},
            'id': {'in_list': {'value': ['test', 'tol_production']}}
        }
        ret = list(qds.get_list('data_source_instance', object_filters=f))
        obj_ids = [obj.id for obj in ret]
        assert 'test' in obj_ids
        assert 'tol_production' in obj_ids
        assert len(obj_ids) == 2
        for obj in ret:
            if obj.id == 'test':
                assert 'test' == obj.id
                assert obj.direct_name == 'elastic'
                assert obj.api_name == 'portal'
                assert obj.publish
            elif obj.id == 'tol_production':
                assert 'tol_production' == obj.id
                assert obj.direct_name == 'elastic'
                assert obj.api_name == 'portal'
                assert obj.publish
