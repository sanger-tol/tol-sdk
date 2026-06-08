# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..bold import create_bold_datasource
from ..copo import create_copo_datasource
from ..ena import create_ena_datasource
from ..goat import create_goat_datasource
from ..jira import create_jira_datasource
from ..labwhere import create_labwhere_datasource
from .defaults import Defaults
from .registry import DataSourceRegistry, EnvVar, SourceDefinition


def register_service_sources(registry: DataSourceRegistry) -> None:
    """Register all service-based DataSource definitions."""

    # BOLD
    registry.register('bold', SourceDefinition(
        factory=create_bold_datasource,
        env_mapping={
            'bold_url_base': EnvVar('BOLD_URL', Defaults.BOLD_URL),
            'bold_api_path': EnvVar('BOLD_API_PATH', Defaults.BOLD_API_PATH),
            'bold_portal_url_base': EnvVar('BOLD_PORTAL_URL', Defaults.BOLD_PORTAL_URL),
            'bold_api_key': EnvVar('BOLD_API_KEY'),
        },
        compose_args={
            'bold_url': ['bold_url_base', 'bold_api_path'],
            'bold_portal_url': ['bold_portal_url_base', 'bold_api_path'],
        },
    ))

    # GoAT
    registry.register('goat', SourceDefinition(
        factory=create_goat_datasource,
        env_mapping={
            'goat_url_base': EnvVar('GOAT_URL', Defaults.GOAT_URL),
            'goat_api_path': EnvVar('GOAT_API_PATH', Defaults.GOAT_API_PATH),
        },
        compose_args={
            'goat_url': ['goat_url_base', 'goat_api_path'],
        },
    ))

    # COPO
    registry.register('copo', SourceDefinition(
        factory=create_copo_datasource,
        env_mapping={
            'copo_url_base': EnvVar('COPO_URL', Defaults.COPO_URL),
            'copo_api_path': EnvVar('COPO_API_PATH', Defaults.COPO_API_PATH),
        },
        compose_args={
            'copo_url': ['copo_url_base', 'copo_api_path'],
        },
    ))

    # Labwhere
    registry.register('labwhere', SourceDefinition(
        factory=create_labwhere_datasource,
        env_mapping={
            'labwhere_url_base': EnvVar('LABWHERE_URL', Defaults.LABWHERE_URL),
            'labwhere_api_path': EnvVar('LABWHERE_API_PATH', Defaults.LABWHERE_API_PATH),
        },
        compose_args={
            'labwhere_url': ['labwhere_url_base', 'labwhere_api_path'],
        },
    ))

    # ENA
    registry.register('ena', SourceDefinition(
        factory=create_ena_datasource,
        env_mapping={
            'ena_url': EnvVar('ENA_URL', Defaults.ENA_URL),
            'ena_user': EnvVar('ENA_USER'),
            'ena_password': EnvVar('ENA_PASSWORD'),
            'ena_contact_name': EnvVar('ENA_CONTACT_NAME'),
            'ena_contact_email': EnvVar('ENA_CONTACT_EMAIL'),
        },
    ))

    # Jira (GRIT)
    registry.register('grit', SourceDefinition(
        factory=create_jira_datasource,
        env_mapping={
            'jira_url': EnvVar('JIRA_URL', Defaults.JIRA_URL),
            'jira_api_key': EnvVar('JIRA_API_KEY'),
        },
    ))
