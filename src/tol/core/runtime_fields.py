# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class RuntimeField:
    """
    The Python representation of a field that is evaluated at runtime.
    A RuntimeField can be either a generic function with name and parameters
    (when `function` and `function_kwargs` are provided) or by a domain-specific script string
    (when a `script`) is provided
    """
    script: str | None = None
    function: str | None = None
    function_kwargs: dict[str, str | RuntimeField] | None = None

    def __post_init__(self) -> None:
        has_script = self.script is not None
        has_function_info = self.function is not None and self.function_kwargs is not None

        if has_script == has_function_info:
            raise ValueError(
                'A runtime field must be either a source-specific script variant '
                '(has the `script` attribute) or a source-independent function variant '
                '(has the `function` and `function_kwargs` attributes)'
            )
