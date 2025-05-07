# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (
    TestCase
)

from tol.sources.bioscan_extra import (
    bioscan_extra
)


class TestBioscanExtraNewPantheonDataSource(TestCase):

    def test_attribute_types(self):
        bds = bioscan_extra()

        assert 'pantheon_species' in bds.attribute_types
        assert bds.attribute_types['pantheon_species']['vernacular'] == 'str'
        assert bds.attribute_types['pantheon_species']['current_conservation_status'] == 'str'
        assert bds.attribute_types['pantheon_species']['larval_feeding_guild'] == 'str'
        assert bds.attribute_types['pantheon_species']['adult_feeding_guild'] == 'str'
        assert bds.attribute_types['pantheon_species']['broad_biotope_habitat_resources'] == 'str'
        assert bds.attribute_types['pantheon_species']['specific_assemblage_type'] == 'str'
        assert bds.attribute_types['pantheon_species']['associations'] == 'str'
        assert bds.attribute_types['pantheon_species']['link_to_assemblage'] == 'str'

    def test_get_list_bioscan_extra(self):
        bds = bioscan_extra()

        ret = bds.get_list('pantheon_species')
        obj = next(ret)
        assert obj.current_conservation_status is not None
