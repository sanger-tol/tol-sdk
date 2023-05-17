# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from itertools import chain
from typing import Iterable, List, Set

from .load import LoadedDataObject
from ..core import DataSourceError


class UpsertValidationError(DataSourceError):
    """Indicates Upsert request data failed validation."""
    def __init__(self, detail: str) -> None:
        super().__init__(
            'Validation Error',
            detail=detail,
            status_code=400
        )


class UpsertValidator(ABC):
    """
    Validates the serialised data of an Upsert request.
    """

    @abstractmethod
    def validate(self, upsert_objects: List[LoadedDataObject]) -> None:
        """
        Validates a list of LoadedDataObject instances according
        to internal criteria.
        """


class DefaultUpsertValidator(UpsertValidator):
    def validate(self, upsert_objects: List[LoadedDataObject]) -> None:
        """
        Validates Upsert data:

        - no upsert UUID's are repeated
        - all relationship UUID's exist
        """
        self.__upsert_objects = upsert_objects
        self.__validate_uuids_unique()
        self.__validate_claimed_uuids()

    def __validate_uuids_unique(self) -> None:
        duplicate_uuids = self.__get_duplicate_uuids()
        if len(duplicate_uuids) > 0:
            detail = (
                'The following request-internal UUID were duplicated: '
                f'"{", ".join(duplicate_uuids)}".'
            )
            raise UpsertValidationError(detail)

    def __get_duplicate_uuids(self) -> Set[str]:
        seen_uuids = set()
        return {
            o._request_uuid for o in self.__upsert_objects
            if o._request_uuid in seen_uuids
            or seen_uuids.add(o._request_uuid)
        }

    def __validate_claimed_uuids(self) -> None:
        non_existent_uuids = self.__get_non_existent_uuids()
        if len(non_existent_uuids) > 0:
            detail = (
                'The following request-internal UUIDs were specified '
                'in relationships, but have no defined object: '
                f'"{", ".join(non_existent_uuids)}".'
            )
            raise UpsertValidationError(detail)

    def __get_non_existent_uuids(self) -> Set[str]:
        existing_uuids = self.__get_existing_uuids()
        claimed_uuids = self.__get_claimed_uuids()
        return claimed_uuids.difference(existing_uuids)

    def __get_existing_uuids(self) -> Set[str]:
        return {o._request_uuid for o in self.__upsert_objects}

    def __get_claimed_uuids(self) -> Set[str]:
        return set(
            chain(
                self.__get_to_one_uuids(),
                self.__get_to_many_uuids()
            )
        )

    def __get_to_one_uuids(self) -> Iterable[str]:
        return chain(*[
            o._one_uuids.values()
            for o in self.__upsert_objects
        ])

    def __get_to_many_uuids(self) -> Iterable[str]:
        return chain(*[
            chain(*list(o._many_uuids.values()))
            for o in self.__upsert_objects
        ])
