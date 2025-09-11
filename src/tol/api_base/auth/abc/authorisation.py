# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT
from abc import ABC, abstractmethod
from typing import Any


class AuthorisationManager(ABC):
    """
    Abstract base class for managing user authorisations and memberships.

    This class defines the interface for authorisation managers that need to
    retrieve user membership information for access control purposes. Concrete
    implementations should handle the specific logic for querying user memberships
    from various authorisation systems (e.g., LDAP, database, external services).

    The class follows the ABC (Abstract Base Class) pattern to ensure that all
    concrete implementations provide the required methods for authorisation
    management.
    """

    @abstractmethod
    def get_user_memberships(self, user: Any) -> list[str]:
        """
        Retrieve the list of group memberships for a given user.

        This method should be implemented by concrete subclasses to fetch
        the user's membership information from the appropriate authorisation
        source. The memberships are typically used to determine what resources
        or actions the user is authorised to access.

        Args:
            user (Any): The user object or identifier for which to retrieve
                       memberships. The type is flexible to accommodate
                       different user representation formats (e.g., user ID,
                       user object, username string, etc.).

        Returns:
            list[str]: A list of group names or membership identifiers that
                      the user belongs to. Returns an empty list if the user
                      has no memberships or if the user is not found.

        Raises:
            NotImplementedError: If called on the abstract base class directly
                               rather than on a concrete implementation.

        Note:
            Concrete implementations may raise additional exceptions specific
            to their authorisation backend (e.g., connection errors, authentication
            failures, etc.).
        """
