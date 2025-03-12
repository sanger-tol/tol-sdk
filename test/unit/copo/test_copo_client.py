# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import responses

from tol.copo.client import CopoApiClient


FAKE_API_URL = 'http://test.lan/api'


class TestCopoApiClient:
    """The `CopoApiClient` and its methods"""

    @responses.activate
    def test_get_detail_manifest(self):
        """Default values, no token"""

        client = CopoApiClient(FAKE_API_URL)
        expected = [{
            'copo_id': 'hype',
            'tolsdk-type': 'manifest'
        }]

        responses.get(
            f'{FAKE_API_URL}/manifest/hype',
            json={
                'status': 'OK',
                'number_found': 1,
                'data': []
            }
        )

        observed = client.get_detail('manifest', ['hype'])
        assert list(observed) == expected

    @responses.activate
    def test_get_detail_samples(self):
        """Default values, no token"""

        client = CopoApiClient(FAKE_API_URL)
        expected = [
            {
                'copo_id': 'hype',
                'attribute1': 'att1'
            }, {
                'copo_id': 'train',
                'attribute1': 'att2'
            }
        ]

        responses.get(
            f'{FAKE_API_URL}/sample/copo_id/hype',
            json={
                'status': 'OK',
                'number_found': 1,
                'data': [
                    {
                        'copo_id': 'hype',
                        'attribute1': 'att1'
                    }
                ]
            }
        )
        responses.get(
            f'{FAKE_API_URL}/sample/copo_id/train',
            json={
                'status': 'OK',
                'number_found': 1,
                'data': [
                    {
                        'copo_id': 'train',
                        'attribute1': 'att2'
                    }
                ]
            }
        )

        observed = client.get_detail('sample', ['hype', 'train'])
        assert list(observed) == expected

    @responses.activate
    def test_get_detail_samples_in_manifest(self):
        """Default values, no token"""

        client = CopoApiClient(FAKE_API_URL)
        expected = [{
            'copo_id': 'hype',
            'tolsdk-type': 'sample',
            'attribute1': 'att1'
        }, {
            'copo_id': 'train',
            'tolsdk-type': 'sample',
            'attribute1': 'att2'
        }]

        responses.get(
            f'{FAKE_API_URL}/manifest/hype',
            json={
                'status': 'OK',
                'number_found': 2,
                'data': [
                    {
                        'copo_id': 'hype',
                        'attribute1': 'att1',
                        'tolsdk-type': 'sample'
                    }, {
                        'copo_id': 'train',
                        'attribute1': 'att2',
                        'tolsdk-type': 'sample'
                    }
                ]
            }
        )

        observed = client.get_samples_in_manifest('hype')
        assert list(observed) == expected
