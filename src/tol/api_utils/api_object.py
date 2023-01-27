# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict

from caseconverter import (
    camelcase,
    snakecase
)


class ApiObject(object):

    def __init__(self, type_, id_, attributes):
        super(ApiObject, self).__init__()
        self._id = id_
        self._type = type_
        self.update_attributes_from_json(attributes)

    @classmethod
    def create(cls, json_obj: Dict):
        return ApiObject(json_obj['type'],
                         json_obj['id'],
                         json_obj['attributes'])

    @property
    def type(self):  # noqa A003
        return self._type

    @property
    def id(self):  # noqa A003
        return self._id

    def update_attributes_from_json(self, json_attributes):
        self.attributes = {snakecase(k): v for k, v in json_attributes.items()}
        for k, v in self.attributes.items():
            setattr(self, k, v)

    def to_json(self):
        return {'id': self._id,
                'type': self.type,
                'attributes': {camelcase(k): v for k, v in self.attributes.items()}}
