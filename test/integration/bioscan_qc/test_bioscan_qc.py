# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase
)

from tol.sources.bioscan_qc import (
    bioscan_qc
)


class TestBioscanQcDataSource(TestCase):

    def test_attribute_types(self):
        bds = bioscan_qc()

        assert 'specimen' in bds.attribute_types
        assert bds.attribute_types['specimen']['sanger_qc_result'] == 'str'
        assert bds.attribute_types['specimen']['sanger_qc_description'] == 'str'

        assert 'uksi_entry' in bds.attribute_types
        assert bds.attribute_types['uksi_entry']['uksi_name_status'] == 'str'

    def test_get_list_qc(self):
        bds = bioscan_qc()

        ret = bds.get_list('specimen')
        obj = next(ret)
        assert obj.sanger_qc_result is not None
        assert obj.sanger_qc_description is not None

    def test_get_list_uksi(self):
        bds = bioscan_qc()

        ret = bds.get_list('uksi_entry')
        obj = next(ret)
        assert obj.uksi_name_status is not None
