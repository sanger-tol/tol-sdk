# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class AttributeMetadata(ABC):
    @abstractmethod
    def get_display_name(
            self,
            object_type: str,
            attribute_name: str) -> str:
        """
        Gets the attribute display name
        """

    @abstractmethod
    def is_available_on_relationships(
            self,
            object_type: str,
            attribute_name: str) -> bool:
        """
        Is the attribute available on a to_one related object?
        This is not always the case, for example in elastic, only
        enriched attributes will be available.
        """

    @abstractmethod
    def get_cardinality(
            self,
            object_type: str,
            attribute_name: str) -> Optional[int]:
        """
        The approximate cardinality of the attribute, i.e. how many different
        values there are. This can be used for making decisions in the UI
        about how to display or filter.
        """

    @abstractmethod
    def get_description(
            self,
            object_type: str,
            attribute_name: str) -> Optional[str]:
        """
        The description of an attribute. This would normally be fetched from
        and underlying metadata store.
        """

    @abstractmethod
    def get_source(
            self,
            object_type: str,
            attribute_name: str) -> Optional[str]:
        """
        The source of the attribute i.e becnhling, sts etc
        """

    @abstractmethod
    def is_authoritative(
        self,
        object_type: str,
        attribute_name: str
    ) -> bool:
        pass


class DefaultAttributeMetadata(AttributeMetadata):
    def get_display_name(
            self,
            object_type: str,
            attribute_name: str) -> str:
        parts = attribute_name.split('_')
        words = []
        for part in parts:
            words.append(self.__normalise_word(part))
        return ' '.join(words)

    def __normalise_word(self, word: str) -> str:
        replacements = {
            'id': 'ID',
            'uid': 'UID',
            'sts': 'STS',
            'tolqc': 'ToLQC',
            'tolid': 'ToLID',
            'tol': 'ToL',
            'eln': 'ELN',
            'dna': 'DNA',
            'rna': 'RNA',
            'mlwh': 'MLWH'
        }
        if word in replacements:
            return replacements[word]
        return word.capitalize()

    def is_available_on_relationships(
            self,
            object_type: str,
            attribute_name: str) -> bool:
        """
        Is the attribute available on a to_one related object?
        This is not always the case, for example in elastic, only
        enriched attributes will be available.
        """
        return True

    def is_authoritative(
            self,
            object_type: str,
            attribute_name: str) -> bool:
        """
        Is the attribute authoritative (i.e. there are other options for this
        piece of data but this one is the most trusted)
        """
        return True

    def get_cardinality(
            self,
            object_type: str,
            attribute_name: str) -> Optional[int]:
        """
        The approximate cardinality of the attribute, i.e. how many different
        values there are. This can be used for making decisions in the UI
        about how to display or filter.
        """
        return None

    def get_description(
            self,
            object_type: str,
            attribute_name: str) -> Optional[str]:
        """
        The description of an attribute. This would normally be fetched from
        and underlying metadata store.
        """
        return None

    def get_source(
            self,
            object_type: str,
            attribute_name: str) -> Optional[str]:
        """
        The source of the attribute i.e becnhling, sts etc
        """
        return None
