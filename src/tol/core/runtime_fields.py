# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class RuntimeField:
    """
    The Python representation of a field that is evaluated at runtime.
    A RuntimeField can be either a generic function with name and parameters
    (when `function` and `function_kwargs` are provided) or by a domain-specific script string
    (when a `script`) is provided
    """
    # Script variant
    script: str | None = None
    type: str | None = None

    # Function variant
    function: str | None = None
    function_kwargs: dict[str, str | RuntimeField] | None = None

    def __post_init__(self) -> None:
        has_script_info = self.script is not None and self.type is not None
        has_function_info = self.function is not None and self.function_kwargs is not None

        if has_script_info == has_function_info:
            raise ValueError(
                'A runtime field must be either a source-specific script variant '
                '(has the `script` attribute) or a source-independent function variant '
                '(has the `function` and `function_kwargs` attributes)'
            )


class RuntimeFields(ABC):
    """
    The base class defining methods for generating runtime fields in the format appropriate for
    the subclass's associated datasource.
    """
    @abstractmethod
    @classmethod
    def convert_to_request(cls, runtime_field: RuntimeField):
        """
        Converts a `RuntimeField` to the format used in this datasource
        """
        raise NotImplementedError()

    @classmethod
    def convert_to_request_dict(cls, runtime_field_dict: dict[str, RuntimeField]) -> dict:
        """
        Converts a dict of `RuntimeField`s to a dict of the format used in this datasource
        """
        return {
            key: cls.convert_to_request(runtime_field)
            for key, runtime_field in runtime_field_dict.items()
        }

    @classmethod
    def generate_script_for_function(cls, function: str, **function_kwargs):
        generator = getattr(cls, f'{function}_script')
        return generator(**function_kwargs)

    @abstractmethod
    @classmethod
    def date_interval_script(cls, start_date: str, end_date: str, unit: str = 'days'):
        """
        Generates the script for the date_interval function, in the format used in this datasource
        """
        raise NotImplementedError()

    @abstractmethod
    @classmethod
    def latest_date_script(cls, date_fields: list[str], allow_missing: bool = True):
        """
        Generates the script for the latest_date function, in the format used in this datasource
        """
        raise NotImplementedError()

    @abstractmethod
    @classmethod
    def math_script(
        cls,
        first: str,
        second: str,
        operation: str = '/',
        return_type: str = 'double'
    ):
        """
        Generates the script for the math function, in the format used in this datasource
        """
        raise NotImplementedError()

    @abstractmethod
    @classmethod
    def coalesce_script(
        cls,
        fields: list[str],
        return_type: str = 'keyword',
        null_wins: bool = False
    ):
        """
        Generates the script for the coalesce function, in the format used in this datasource
        """
        raise NotImplementedError()

    @abstractmethod
    @classmethod
    def substring_script(cls, field: str, start: int, end: int, return_type: str = 'keyword'):
        """
        Generates the script for the substring function, in the format used in this datasource
        """
        raise NotImplementedError()
    
