# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase
)

from tol.sources.library_batch_ids import library_batch_ids


class TestLibraryBatchIdsDataSource(TestCase):

    def test_attribute_types(self):
        bds = library_batch_ids()

        assert 'sequencing_request' in bds.attribute_types
        assert bds.attribute_types['sequencing_request']['id'] == 'str'
        assert bds.attribute_types['sequencing_request']['library_batch_id'] == 'str'

    def test_get_list_library_batch_ids(self):
        bds = library_batch_ids()

        ret = bds.get_list('sequencing_request')
        obj = next(ret, None)
        assert obj is not None, 'No sequencing_request data available'
        assert obj.id is not None
        assert obj.library_batch_id is not None
