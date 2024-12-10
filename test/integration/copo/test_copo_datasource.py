# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import (
    TestCase
)

import pytz

from tol.sources.copo import (
    copo
)


class TestCopoDataSource(TestCase):

    def test_attribute_types(self):
        cds = copo()

        assert 'manifest' in cds.attribute_types
        assert 'sample' in cds.attribute_types
        assert cds.attribute_types['sample']['tol_project'] == 'str'
        assert cds.attribute_types['sample']['time_created'] == 'datetime'

    def test_relationship_config(self):
        cds = copo()
        assert 'manifest' in cds.relationship_config
        assert cds.relationship_config['manifest'].to_many['samples'] == 'sample'
        assert 'sample' in cds.relationship_config
        assert cds.relationship_config['sample'].to_one['manifest'] == 'manifest'

    def test_get_by_id_manifest(self):
        cds = copo()
        ret = cds.get_by_id('manifest', ['8bdb1a76-f11d-4322-b1c0-d099b14b603f'])
        obj1 = next(ret)
        assert '8bdb1a76-f11d-4322-b1c0-d099b14b603f' == obj1.id
        # Just pick out a few attributes here to test
        samples = list(obj1.samples)
        assert len(samples) == 5
        assert samples[0].id == '671b8c96d10362e252e21848'
        assert samples[0].tol_project == 'erga'

        with self.assertRaises(StopIteration):
            next(ret)

    def test_get_by_id_sample(self):
        cds = copo()
        ret = cds.get_by_ids('sample', ['5fd21410f18d93000119ca24'])
        obj1 = next(ret)
        assert '5fd21410f18d93000119ca24' == obj1.id
        # Just pick out a few attributes here to test
        assert obj1.biosampleAccession == 'SAMEA7703214'
        assert obj1.time_created == datetime(2020, 12, 10, 12, 26, 56, tzinfo=pytz.UTC)
        assert obj1.tol_project == 'DTOL'
        assert obj1.manifest.id == '789c66d2-5487-450a-a091-471653876542'
        with self.assertRaises(StopIteration):
            next(ret)
