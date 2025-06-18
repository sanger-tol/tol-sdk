# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import typing
from abc import ABC
from typing import Iterable, List


if typing.TYPE_CHECKING:
    from ..data_object import DataObject


class Enricher(ABC):
    """
    Enriches attributes of one object onto relationships of another object
    """

    @property
    def enriching_fields(self):
        """
        Returns a dictionary of object types and their enriching fields
        e.g. {'species': ['goat_family', 'goat_genome_size']}
        """
        object_enriching_fields = {}
        for object_type, attributes in self.attribute_metadata.items():
            enriching_fields = []
            for attribute, metadata in attributes.items():
                if metadata['available_on_relationships']:
                    enriching_fields.append(attribute)
            if len(enriching_fields) > 0:
                object_enriching_fields[object_type] = enriching_fields
        return object_enriching_fields

    @property
    def relationships_to_enrich(self):
        """
        Returns a dictionary of object types and their relationships to enrich for
        each source object type
        e.g. {'extraction': {'species': ['sts_species', 'benchling_species]}}
        """
        relationships_to_enrich = {}
        for object_type, rc in self.relationship_config.items():
            if rc.to_one is not None:
                for rel_name, related_object_type in rc.to_one.items():
                    if related_object_type not in relationships_to_enrich:
                        relationships_to_enrich[related_object_type] = {}
                    if object_type not in relationships_to_enrich[related_object_type]:
                        relationships_to_enrich[related_object_type][object_type] = []
                    relationships_to_enrich[related_object_type][object_type].append(rel_name)
        return relationships_to_enrich

    def get_enrich_update(
            self,
            enriching_fields: List[str],
            source_data: Iterable[DataObject],
            target_object_type: str
    ):
        """
        Gets the update data for enriching an index with the source fields
        Makes an update if the id of the target attribute is present (candidate_key).

        args:
            source_fields: list of fields to enrich the index with
            source_data: elastic.get_list data returned by the source_index
            target_object_type: the object type of the target index
        """
        for obj in source_data:
            obj_dict = {'id': obj.id}
            # Get the values of the enriching fields
            for field in enriching_fields:
                obj_dict[field] = obj.get_field_by_name(field)
            for target_attribute in self.relationships_to_enrich[obj.type][target_object_type]:
                yield (
                    None,
                    {
                        f'{target_attribute}': obj_dict,
                        f'{target_attribute}.id': obj.id  # The candidate key
                    }
                )

    def enrich(
            self,
            source_object_type: str,
            source_objects: Iterable[DataObject],
            target_object_type: str):
        """
        Enriches the target object type with the enriching fields from the source object type
        """
        if source_object_type in self.enriching_fields:
            updates = self.get_enrich_update(
                self.enriching_fields[source_object_type],
                source_objects,
                target_object_type
            )
            candidate_key_possibilities = [
                f'{rel}.id'
                for rel in self.relationships_to_enrich[source_object_type][target_object_type]
            ]
            self.update(
                target_object_type,
                updates,
                candidate_key_func=lambda x:
                    [next((key for key in candidate_key_possibilities if key in x))]
            )
