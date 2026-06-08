# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable

from ..core import core_data_object
from ..core.datasource import DataSource


@dataclass(frozen=True)
class EnvVar:
    """A reference to an environment variable with an optional default."""

    name: str
    default: str | None = None

    def resolve(self) -> str | None:
        return os.getenv(self.name, self.default)


@dataclass(frozen=True)
class SourceDefinition:
    """Declarative definition of how to create a DataSource."""

    factory: Callable[..., DataSource]
    env_mapping: dict[str, EnvVar] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)
    compose_args: dict[str, list[str]] | None = None

    def resolve(self, **overrides: Any) -> dict[str, Any]:
        resolved = {}
        for kwarg_name, env_var in self.env_mapping.items():
            resolved[kwarg_name] = env_var.resolve()
        resolved.update(self.defaults)
        if self.compose_args:
            for target, parts in self.compose_args.items():
                resolved[target] = ''.join(
                    str(resolved.pop(p, '') or '') for p in parts
                )
        resolved.update(overrides)
        return resolved


class DataSourceRegistry:
    """
    A registry that stores declarative DataSource definitions and
    creates configured DataSource instances on demand.
    """

    def __init__(self) -> None:
        self._definitions: dict[str, SourceDefinition] = {}

    def register(self, name: str, definition: SourceDefinition) -> None:
        self._definitions[name] = definition

    @property
    def available_sources(self) -> list[str]:
        return list(self._definitions.keys())

    def create(self, name: str, **overrides: Any) -> DataSource:
        if name not in self._definitions:
            raise KeyError(
                f"Unknown source: '{name}'. Available: {self.available_sources}"
            )
        defn = self._definitions[name]
        kwargs = defn.resolve(**overrides)
        ds = defn.factory(**kwargs)
        core_data_object(ds)
        return ds


# Module-level default registry instance
default_registry = DataSourceRegistry()
