from apispec_webframeworks.tornado import TornadoPlugin

from .webargs_plugin import WebargsPlugin


class TornadoWebargsPlugin(WebargsPlugin, TornadoPlugin):
    def __init__(self):
        raise NotImplementedError("Tornado is not currently supported")

    def path_helper(self, operations, parameters, *, view, app=None, **kwargs):
        raise NotImplementedError("Tornado is not currently supported")

    def operation_helper(self, operations, *, view, **kwargs):
        raise NotImplementedError("Tornado is not currently supported")
