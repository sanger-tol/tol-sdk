from .authorization import NeedABC

class NeedsFactory:
    def __init__(
        self,
        object_type: str,
    ):
        self.object_type = object_type
        self.method = method
        self.need_class = namedtuble(self.object_type, ['method','value'])
        self.needs = needs

    def build_needs(self, needs: list[any]):
        need_objects = []
        for need in needs:
            if hasattr(need, 'methods'):
                for method in methods:
                    need_objects.append(self.build_need(method.name))

        return need_objects

    def build_need(self, method: str):
        return self.need_class(method)
