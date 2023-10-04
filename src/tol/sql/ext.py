# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from typing import Any, Callable

from sqlalchemy import Column, JSON
from sqlalchemy.orm import declared_attr

if typing.TYPE_CHECKING:
    from .model import Model


def ext(
    cls: type[Model] | None = None,
    *,
    column_name: str = 'ext',
    column_factory: Callable[[], Column] = lambda: Column(JSON)
) -> Callable[[type[Model]], type[Model]] | type[Model]:
    """
    This cannot be used to correctly create a table containing an ext column

    A decorator that adds an "ext" column to a `Model`.

    This column supports a (for now ReadOnly) dynamic "promotion"
    of entries within its JSON object to top-level entries in the
    property `Model().instance_attributes`.

    Can be decorated either with or without parentheses, the latter of
    which supports overriding the `column_name` and `column_factory`.
    """

    if cls is not None:
        @declared_attr
        def ext_column(self):
            return column_factory()

        ext_column.__name__ = column_name
        setattr(cls, column_name, ext_column)

        def exclude_wrapper(
            cls_fn: Callable[[], list[str]]
        ) -> Callable[[], list[str]]:

            def inner() -> list[str]:
                excluded = cls_fn()
                return [
                    *excluded,
                    column_name
                ]

            return inner

        cls.get_excluded_column_names = exclude_wrapper(
            cls.get_excluded_column_names
        )

        def attrs_wrapper(_property: property) -> property:

            @property
            def inner(self: Model) -> dict[str, Any]:
                ext_attrs = getattr(self, column_name)
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
        return ext(
            cls,
            column_name=column_name,
            column_factory=column_factory
        )

    return decorator
