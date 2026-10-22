# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT


import os
from uuid import uuid4

import pytest

from tol.sources.prefect import prefect


class TestPrefectDataSource:

    @pytest.fixture
    def staging(self):
        keys = (
            'PREFECT_URL',
            'PREFECT_API_PATH',
            'TEST_PREFECT_FLOW_NAME',
            'TEST_PREFECT_DEPLOYMENT_NAME',
        )
        if not all(os.getenv(key) for key in keys):
            pytest.skip('Staging Prefect configuration is required')

        datasource = prefect()
        return (
            datasource,
            os.environ['TEST_PREFECT_FLOW_NAME'],
            os.environ['TEST_PREFECT_DEPLOYMENT_NAME'],
        )


    def test_insert_and_get_flow_run(self, staging):
        datasource, flow_name, deployment_name = staging
        attributes = {
            'flow_name': flow_name,
            'deployment_name': deployment_name,
            'name': f'sdk-integration-{uuid4()}',
            'tags': ['sdk-integration'],
            'idempotency_key': str(uuid4()),
            'parameters': {},
        }
        candidate = datasource.data_object_factory(
            'flow_run', attributes=attributes
        )
        inserted = list(datasource.insert('flow_run', [candidate]))[0]

        try:
            fetched = datasource.get_one('flow_run', inserted.id)
            assert fetched is not None
            assert fetched.id == inserted.id
            for key in attributes:
                if key != 'tags':
                    assert fetched.attributes[key] == attributes[key]
            assert 'sdk-integration' in fetched.tags
            assert fetched.state == 'Scheduled'
        finally:
            datasource.delete('flow_run', [inserted.id])

        assert datasource.get_one('flow_run', inserted.id) is None


    def test_get_missing_flow_run(self, staging):
        datasource, _, _ = staging
        assert datasource.get_one('flow_run', str(uuid4())) is None