# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeField:
    """
    The Python representation of a runtime field, as specified in the database
    (from a `runtime_definition` column).

    Every runtime field must specify a return `type`. This is the type from the source being
    worked with, not the Python type. A runtime field can then either contain a `script` in the
    domain-specific format required for the data source, or a standard function, specified by
    `function`, with its arguments provided in `function_kwargs`.
    """
    type_: str
    script: str | None = None
    function: str | None = None
    function_kwargs: dict[str, Any | RuntimeField] | None = None


class RuntimeFields(ABC):
    """
    The base class defining methods for generating runtime fields in the format appropriate for
    the subclass's associated datasource.
    """
    @classmethod
    @abstractmethod
    def convert_to_request(cls, runtime_field: RuntimeField):
        """
        Converts a `RuntimeField` to the format used in this datasource
        """

    @classmethod
    def convert_to_request_dict(cls, runtime_field_dict: dict[str, RuntimeField]) -> dict:
        """
        Converts a dict of `RuntimeField`s to a dict of the format used in this datasource
        """
        return {
            name: cls.convert_to_request(runtime_field)
            for name, runtime_field in runtime_field_dict.items()
        }

    @classmethod
    @abstractmethod
    def date_interval_script(cls, *, start_date: str, end_date: str, unit: str = 'days'):
        """
        Generates the script for the date_interval function, in the format used in this datasource
        """

    @classmethod
    @abstractmethod
    def latest_date_script(cls, *, date_fields: list[str], allow_missing: bool = True):
        """
        Generates the script for the latest_date function, in the format used in this datasource
        """

    @classmethod
    @abstractmethod
    def math_script(
        cls,
        *,
        first: str,
        second: str,
        operation: str = '/'
    ):
        """
        Generates the script for the math function, in the format used in this datasource
        """

    @classmethod
    @abstractmethod
    def coalesce_script(
        cls,
        *,
        _return_type: str,
        fields: list[str],
        null_wins: bool = False,
    ):
        """
        Generates the script for the coalesce function, in the format used in this datasource
        """

    @classmethod
    @abstractmethod
    def substring_script(
        cls,
        *,
        field: str,
        start: int,
        end: int
    ):
        """
        Generates the script for the substring function, in the format used in this datasource
        """
