# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from unittest import (TestCase)

from tol.utils import convert_s3_to_https


class TestS3(TestCase):
    def test_convert_s3_to_https(self):
        expected = 'https://my-bucket.cog.sanger.ac.uk/my/path'
        result = convert_s3_to_https('s3://my-bucket/my/path')
        self.assertEqual(expected, result)

    def test_convert_s3_to_https_no_path(self):
        expected = 'https://my-bucket.cog.sanger.ac.uk/'
        result = convert_s3_to_https('s3://my-bucket/')
        self.assertEqual(expected, result)

    def test_convert_s3_to_https_invalid(self):
        expected = 'invalid_s3_path'
        result = convert_s3_to_https('invalid_s3_path')
        self.assertEqual(expected, result)
