# SPDX-FileCopyrightText: 2023 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

from typing import Dict

from flask_restx import Namespace, fields as restx_fields


class Swagger:
    def __init__(self, name: str, fields: Dict[str, restx_fields.Raw]):
        self.name = name
        self.fields = fields

    def to_namespace_model(self, ns: Namespace) -> Namespace.model:
        return ns.model(
            self.name,
            self.fields
        )
