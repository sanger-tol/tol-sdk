# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict

from caseconverter import (
    snakecase
)


class OldApiObject(object):

    def __init__(self, type_, id_, attributes={}, relationships={}):
        super(OldApiObject, self).__init__()
        self._id = id_
        self._type = type_
        self.update_attributes_from_dict(attributes)
        self.update_relationships_from_dict(relationships)

    @classmethod
    def create(cls, json_obj: Dict):
        return OldApiObject(
            json_obj['type'],
            json_obj['id'],
            json_obj.get('attributes', {}),
            json_obj.get('relationships', {})
        )

    @property
    def type(self):  # noqa A003
        return self._type

    @property
    def id(self):  # noqa A003
        return self._id

    def update_attributes_from_dict(self, json_attributes):
        self.attributes = {snakecase(k): v for k, v in json_attributes.items()}
        for k, v in self.attributes.items():
            setattr(self, k, v)

    def update_relationships_from_dict(self, json_relationships):
        self.relationships = {snakecase(k): v for k, v in json_relationships.items()}
        for k, v in self.relationships.items():
            setattr(self, k, v)

    def to_short_json(self):
        return {'id': self._id,
                'type': self.type}

    def to_json(self):
        return {
            'id': self._id,
            'type': self.type,
            'attributes': {snakecase(k): v for k, v in self.attributes.items()},
            'relationships':
                {snakecase(k): {'data': v.to_short_json()} for k, v in self.relationships.items()}
        }
