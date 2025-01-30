from typing import Any
from collections import namedtuple
from functools import partial
from flask_principal import Need


class NeedsFactory:
    def __init__(
        self,
        object_type: str,
    ):
        self.object_type = object_type
        self.need_class = namedtuple(self.object_type, ['method','value'])

    def build_needs(self, needs: list[Any]):
        need_objects = []
        for need in needs:
            if hasattr(need, 'methods'):
                for method in need.methods:
                    need_objects.append(self.build_need('method', method.identifier))

        return need_objects

    def build_need(self, identifier: str, value: any):
        need_class = partial(self.need_class, identifier)
        return need_class(value)