# SPDX-FileCopyrightText: 2022 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from ..core import (
    DefaultAttributeMetadata
)


class ElasticAttributeMetadata(DefaultAttributeMetadata):
    attribute_meta = {}

    def is_attribute_available_on_relationships(
            self,
            object_type: str,
            attribute_name: str) -> bool:
        if object_type in self.attribute_meta:
            if attribute_name in self.attribute_meta[object_type]:
                if self.attribute_meta[object_type][attribute_name].get(
                        'available_on_relationships', False):
                    return True
        return False
