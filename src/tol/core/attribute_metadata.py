# SPDX-FileCopyrightText: 2024 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Optional


class AttributeMetadata(ABC):
    @abstractmethod
    def format_string(self, input_string: str) -> str:
        """
        Format a string into another string
        """

    @abstractmethod
    def is_attribute_available_on_relationships(
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
    def get_attribute_description(
            self,
            object_type: str,
            attribute_name: str) -> Optional[str]:
        """
        The description of an attribute. This would normally be fetched from
        and underlying metadata store.
        """


class DefaultAttributeMetadata(AttributeMetadata):
    def format_string(self, input_string: str) -> str:
        parts = input_string.split('_')
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

    def is_attribute_available_on_relationships(
            self,
            object_type: str,
            attribute_name: str) -> bool:
        """
        Is the attribute available on a to_one related object?
        This is not always the case, for example in elastic, only
        enriched attributes will be available.
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

    def get_attribute_description(
            self,
            object_type: str,
            attribute_name: str) -> Optional[str]:
        """
        The description of an attribute. This would normally be fetched from
        and underlying metadata store.
        """
        return None
