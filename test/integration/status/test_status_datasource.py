# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import os
from unittest import (
    TestCase
)

from tol.core import (
    DataSourceFilter,
    core_data_object
)
from tol.status import (
    StatusDataSource
)


def status_data_source() -> StatusDataSource:
    sds = StatusDataSource({})
    core_data_object(sds)
    return sds


class TestStatusDataSource(TestCase):

    def test_attribute_types(self):
        sds = status_data_source()

        assert 'status' in sds.attribute_types
        assert sds.attribute_types['status']['ok'] == 'bool'
        assert sds.attribute_types['status']['status_code'] == 'int'

    def test_get_list_page_sort_id(self):
        sds = status_data_source()

        f = DataSourceFilter(
            and_={
                'id': {
                    'in_list': {
                        'value': [
                            os.getenv('PORTAL_URL'),
                            os.getenv('PORTAL_URL') + os.getenv('PORTAL_API_PATH') + '/nonsense',
                            'http://nothing.tol.sanger.ac.uk'
                        ]
                    }
                }
            }
        )

        ret, total = sds.get_list_page(
            'status',
            page_number=1,
            object_filters=f
        )
        assert total == 3
        assert len(ret) == 3
        assert ret[0].id == 'https://portal-staging.tol.sanger.ac.uk'
        assert ret[0].status_code == 200
        assert ret[0].ok
        assert ret[1].id == 'https://portal-staging.tol.sanger.ac.uk/api/v1/nonsense'
        assert ret[1].status_code == 404
        assert not ret[1].ok
        assert ret[2].id == 'http://nothing.tol.sanger.ac.uk'
        assert ret[2].status_code == 500
        assert not ret[2].ok
