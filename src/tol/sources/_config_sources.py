# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..benchling import BenchlingDataSource
from ..mlwh import MlwhDataSource
from ..sciops import SequencingDataSource
from ..sts import StsDataSource
from .registry import DataSourceRegistry, EnvVar, SourceDefinition


def _create_benchling(**kwargs) -> BenchlingDataSource:
    return BenchlingDataSource(kwargs)


def _create_mlwh(**kwargs) -> MlwhDataSource:
    return MlwhDataSource(kwargs)


def _create_sciops(**kwargs) -> SequencingDataSource:
    return SequencingDataSource(kwargs)


def _create_sts_legacy(**kwargs) -> StsDataSource:
    return StsDataSource(kwargs)


def register_config_sources(registry: DataSourceRegistry) -> None:
    """Register all config-dict based DataSource definitions."""

    # Benchling
    registry.register('benchling', SourceDefinition(
        factory=_create_benchling,
        env_mapping={
            'api_key': EnvVar('BENCHLING_API_KEY'),
            'url': EnvVar('BENCHLING_URL'),
            'registry_id': EnvVar('BENCHLING_REGISTRY_ID'),
            'project_id': EnvVar('BENCHLING_PROJECT_ID'),
        },
    ))

    # MLWH
    registry.register('mlwh', SourceDefinition(
        factory=_create_mlwh,
        env_mapping={
            'uri': EnvVar('MLWH_URI'),
        },
    ))

    # SciOps
    registry.register('sciops', SourceDefinition(
        factory=_create_sciops,
        env_mapping={
            'redpanda_url': EnvVar('REDPANDA_URL'),
            'redpanda_api_key': EnvVar('REDPANDA_API_KEY'),
            'rabbitmq_host': EnvVar('RABBITMQ_HOST'),
            'rabbitmq_port': EnvVar('RABBITMQ_PORT'),
            'rabbitmq_username': EnvVar('RABBITMQ_USERNAME'),
            'rabbitmq_password': EnvVar('RABBITMQ_PASSWORD'),
            'rabbitmq_vhost': EnvVar('RABBITMQ_VHOST'),
            'rabbitmq_exchange': EnvVar('RABBITMQ_EXCHANGE'),
            'rabbitmq_routing_key': EnvVar('RABBITMQ_ROUTING_KEY'),
            'rabbitmq_use_ssl': EnvVar('RABBITMQ_USE_SSL'),
            'rabbitmq_publish_retry_delay': EnvVar('RABBITMQ_PUBLISH_RETRY_DELAY'),
            'rabbitmq_publish_retries': EnvVar('RABBITMQ_PUBLISH_RETRIES'),
            'tol_feedback_queue': EnvVar('TOL_FEEDBACK_QUEUE'),
        },
    ))

    # STS Legacy
    registry.register('sts_legacy', SourceDefinition(
        factory=_create_sts_legacy,
        env_mapping={
            'url_base': EnvVar('STS_LEGACY_URL'),
            'api_path': EnvVar('STS_LEGACY_API_PATH'),
            'key': EnvVar('STS_API_KEY'),
        },
        compose_args={
            'url': ['url_base', 'api_path'],
        },
    ))
