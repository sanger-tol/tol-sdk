# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..api_client import create_api_datasource
from .defaults import Defaults
from .registry import DataSourceRegistry, EnvVar, SourceDefinition


def register_api_sources(registry: DataSourceRegistry) -> None:
    """Register all standard API-based DataSource definitions."""

    api_sources = {
        'portal': {
            'url': EnvVar('PORTAL_URL', Defaults.PORTAL_URL),
            'api_path': EnvVar('PORTAL_API_PATH', Defaults.PORTAL_API_PATH),
            'token': EnvVar('PORTAL_API_KEY'),
            'data_prefix': EnvVar('PORTAL_API_DATA_PATH', Defaults.PORTAL_API_DATA_PATH),
        },
        'sts': {
            'url': EnvVar('STS_URL', Defaults.STS_URL),
            'api_path': EnvVar('STS_API_PATH', Defaults.STS_API_PATH),
            'token': EnvVar('STS_API_KEY'),
            'data_prefix': EnvVar('STS_API_DATA_PATH', Defaults.STS_API_DATA_PATH),
        },
        'tolid': {
            'url': EnvVar('TOLID_URL', Defaults.TOLID_URL),
            'api_path': EnvVar('TOLID_API_PATH', Defaults.TOLID_API_PATH),
            'token': EnvVar('TOLID_API_KEY'),
            'data_prefix': EnvVar('TOLID_API_DATA_PATH', Defaults.TOLID_API_DATA_PATH),
        },
        'tolqc': {
            'url': EnvVar('TOLQC_URL', Defaults.TOLQC_URL),
            'api_path': EnvVar('TOLQC_API_PATH', Defaults.TOLQC_API_PATH),
            'token': EnvVar('TOLQC_API_KEY'),
            'data_prefix': EnvVar('TOLQC_API_DATA_PATH', Defaults.TOLQC_API_DATA_PATH),
        },
        'bioscan': {
            'url': EnvVar('BIOSCAN_URL', Defaults.BIOSCAN_URL),
            'api_path': EnvVar('BIOSCAN_API_PATH', Defaults.BIOSCAN_API_PATH),
            'token': EnvVar('BIOSCAN_API_KEY'),
            'data_prefix': EnvVar('BIOSCAN_API_DATA_PATH', Defaults.BIOSCAN_API_DATA_PATH),
        },
        'treeofsex': {
            'url': EnvVar('TREEOFSEX_URL', Defaults.TREEOFSEX_URL),
            'api_path': EnvVar('TREEOFSEX_API_PATH', Defaults.TREEOFSEX_API_PATH),
            'token': EnvVar('TREEOFSEX_API_KEY'),
            'data_prefix': EnvVar('TREEOFSEX_API_DATA_PATH', Defaults.TREEOFSEX_API_DATA_PATH),
        },
        'workflows': {
            'url': EnvVar('WORKFLOWS_URL', Defaults.WORKFLOWS_URL),
            'api_path': EnvVar('WORKFLOWS_API_PATH', Defaults.WORKFLOWS_API_PATH),
            'token': EnvVar('WORKFLOWS_API_KEY'),
            'data_prefix': EnvVar('WORKFLOWS_API_DATA_PATH', Defaults.WORKFLOWS_API_DATA_PATH),
        },
    }

    for name, env_map in api_sources.items():
        registry.register(name, SourceDefinition(
            factory=create_api_datasource,
            env_mapping=env_map,
            defaults={'retries': 5},
            compose_args={'api_url': ['url', 'api_path']},
        ))

    # portaldb uses the same portal URL but a fixed data_prefix
    registry.register('portaldb', SourceDefinition(
        factory=create_api_datasource,
        env_mapping={
            'url': EnvVar('PORTAL_URL', Defaults.PORTAL_URL),
            'api_path': EnvVar('PORTAL_API_PATH', Defaults.PORTAL_API_PATH),
            'token': EnvVar('PORTAL_API_KEY'),
        },
        defaults={'retries': 5, 'data_prefix': '/local'},
        compose_args={'api_url': ['url', 'api_path']},
    ))
