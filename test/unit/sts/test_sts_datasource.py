# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from datetime import datetime
from unittest import (TestCase, mock)

from tol.core import (
    core_data_object
)
from tol.sts import StsDataSource


class MockStsDataSource(StsDataSource):
    pass


def mock_sts_data_source() -> StsDataSource:
    sts = MockStsDataSource({
        'url': 'http://test/benchling',
        'key': '1234'
    })
    sts.native_post = mock.Mock()
    core_data_object_mock = core_data_object(sts)
    return core_data_object_mock, sts


dt = datetime.fromtimestamp(1234567890)


class TestStsDataSource(TestCase):

    def test_upsert_extraction(self):
        """succesfully instantiates"""
        core_data_object, sts = mock_sts_data_source()

        extraction1 = core_data_object(
            'extraction',
            data={
                'id': 'eln_123',
                'sample_id': 'SAMP123456',
                'fluidx_id': 'FD12345678',
                'extraction_type': 'DNA',
                'extraction_date': dt
            })

        sts.upsert('extraction', [extraction1])

        sts.native_post.assert_called_once()
        sts.native_post.assert_called_with(
            '/ep_samples/FD12345678',
            json={
                'eln_id': 'eln_123',
                'sample_id': 'SAMP123456',
                'fluidx_id': 'FD12345678',
                'type': 'DNA',
                'extraction_date': sts._encode_date(dt)
            }
        )

    def test_upsert_sequencing_request(self):
        """succesfully instantiates"""
        core_data_object, sts = mock_sts_data_source()

        sr1 = core_data_object(
            'sequencing_request',
            data={
                'id': 'REF1234',
                'fluidx_id': 'FD12345678',
                'platform': 'PACBIO',
                'submission_date': dt
            })
        sts.upsert('sequencing_request', [sr1])

        sts.native_post.assert_called_once()
        sts.native_post.assert_called_with(
            '/sequencing-requests',
            json={
                'platform': 'PACBIO',
                'fluidx_id': 'FD12345678',
                'sample_ref': 'REF1234',
                'submit_date': sts._encode_date(dt)
            }
        )
