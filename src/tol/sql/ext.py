# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from typing import Any, Callable

if typing.TYPE_CHECKING:
    from .model import Model


def ext(
    cls: type[Model] | None = None,
    *,
    target: str = 'ext'
) -> Callable[[type[Model]], type[Model]] | type[Model]:
    """
    This column supports a (for now ReadOnly) dynamic "promotion"
    of entries, from a `target` column that produces a `dict` value,
    to top-level entries in the property `Model().instance_attributes`.

    Can be decorated either with or without parentheses, the latter of
    which supports overriding the name of the `target` column.
    """

    if cls is not None:

        def exclude_wrapper(
            cls_fn: Callable[[], list[str]]
        ) -> Callable[[], list[str]]:

            def inner() -> list[str]:
                excluded = cls_fn()
                return [
                    *excluded,
                    target
                ]

            return inner

        cls.get_excluded_column_names = exclude_wrapper(
            cls.get_excluded_column_names
        )

        def attrs_wrapper(_property: property) -> property:

            @property
            def inner(self: Model) -> dict[str, Any]:
                ext_attrs = getattr(self, target)
                return {
                    **(ext_attrs if ext_attrs else {}),
                    **_property.fget(self)
                }

            return inner

        cls.instance_attributes = attrs_wrapper(
            cls.instance_attributes
        )

        return cls

    def decorator(cls: type[Model]) -> type[Model]:
        return ext(cls, target=target)

    return decorator
