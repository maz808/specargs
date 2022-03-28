from apispec_webframeworks.bottle import BottlePlugin

from ..plugin import WebargsPlugin


class BottleWebargsPlugin(WebargsPlugin, BottlePlugin):
    def __init__(self):
        raise NotImplementedError("Bottle is not currently supported")

    def path_helper(self, operations, parameters, *, view, app=None, **kwargs):
        raise NotImplementedError("Bottle is not currently supported")

    def operation_helper(self, operations, *, view, **kwargs):
        raise NotImplementedError("Bottle is not currently supported")
