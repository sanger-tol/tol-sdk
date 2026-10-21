# SPDX-FileCopyrightText: 2026 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass


@dataclass(slots=True)
class FunctionRuntimeField:
    """
    The variant of a runtime field specifying a source-independent function to operate on data
    """
    function: str
    params: dict[str, str | RuntimeField]


RuntimeField = FunctionRuntimeField | str
"""
The Python representation of a field that is evaluated at runtime.
A RuntimeField can be represented by either a generic function with name and parameters
(when an instance of `FunctionRuntimeField`) or by a domain-specific script string (when a `str`)
"""
