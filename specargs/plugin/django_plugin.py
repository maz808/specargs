from .webargs_plugin import WebargsPlugin


class DjangoWebargsPlugin(WebargsPlugin):
    def __init__(self):
        raise NotImplementedError("Django is not currently supported")

    def path_helper(self, operations, parameters, *, view, app=None, **kwargs):
        raise NotImplementedError("Django is not currently supported")

    def operation_helper(self, operations, *, view, **kwargs):
        raise NotImplementedError("Django is not currently supported")
