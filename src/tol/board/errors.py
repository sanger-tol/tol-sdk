# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from ..core import DataSourceError


class NotFoundError(DataSourceError):
    """Raised when a board entity is not found."""

    def __init__(self, object_type: str) -> None:
        """Initialize a NotFoundError."""
        detail = f'The given {object_type} was not found.'
        super().__init__(title='Not Found', detail=detail, status_code=404)


class UnknownTypeError(DataSourceError):
    """Raised when a board entity type is not recognized."""

    def __init__(self) -> None:
        """Initialize an UnknownTypeError."""
        detail = 'The given type is not recognised in the hierarchy'
        super().__init__(title='Unknown Type', detail=detail, status_code=400)


class AddError(DataSourceError):
    """Raised when attempting to add a root-level entity with a parent ID."""

    def __init__(self, object_type: str) -> None:
        """Initialize an AddError."""
        detail = f'Cannot add {object_type} with a parent ID.'
        super().__init__(title='Add Error', detail=detail, status_code=400)


class BadParentError(DataSourceError):
    """Raised when a parent ID does not match the expected parent type."""

    def __init__(self, expected_parent_type: str) -> None:
        """Initialize a BadParentError."""
        detail = f'The parent ID does not match expected type {expected_parent_type}.'
        super().__init__(title='Bad Parent', detail=detail, status_code=400)


class InvalidOrderError(DataSourceError):
    """Raised when child order is invalid or incomplete."""

    def __init__(self) -> None:
        """Initialize an InvalidOrderError."""
        detail = (
            'Not all child IDs are included in the new order, or there are '
            'extra IDs that are not children.'
        )
        super().__init__(title='Invalid Order', detail=detail, status_code=400)


class CopyError(DataSourceError):
    """Raised when an error occurs while copying an entity."""

    def __init__(self, object_type: str) -> None:
        """Initialize a CopyError."""
        detail = f'An error occurred while copying the {object_type}.'
        super().__init__(title='Copy Error', detail=detail, status_code=500)


class DeletionError(DataSourceError):
    """Raised when multiple parent instances point to a child entity."""

    def __init__(self, above_type: str, object_type: str) -> None:
        """Initialize a DeletionError."""
        detail = f'More than one {above_type}s instances point to this {object_type}.'
        super().__init__(title='Deletion Error', detail=detail, status_code=400)
