# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from .registry import (  # noqa: F401
    DataSourceRegistry,
    EnvVar,
    SourceDefinition,
    default_registry,
)
from ._api_sources import register_api_sources
from ._service_sources import register_service_sources
from ._config_sources import register_config_sources

# Populate the default registry with all built-in sources
register_api_sources(default_registry)
register_service_sources(default_registry)
register_config_sources(default_registry)
