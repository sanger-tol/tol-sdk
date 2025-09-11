# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase
)

from tol.sources.bioscan_image import (
    bioscan_image
)


class TestBioscanImageDataSource(TestCase):

    def test_attribute_types(self):
        bds = bioscan_image()

        assert 'object' in bds.attribute_types
        assert bds.attribute_types['object']['bucket_name'] == 'str'
        assert bds.attribute_types['object']['last_modified'] == 'datetime'

    def test_get_list(self):
        bds = bioscan_image()

        ret = bds.get_list('object')
        obj = next(ret)
        assert obj.bucket_name is not None
        assert obj.last_modified is not None
