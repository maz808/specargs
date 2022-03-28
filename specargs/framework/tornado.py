from apispec_webframeworks.tornado import TornadoPlugin
from webargs.tornadoparser import parser

from ..plugin import WebargsPlugin


def get_request_body(request):
    raise NotImplementedError("Tornado is not currently supported")


def create_paths(self, framework_obj):
    raise NotImplementedError("Tornado is not currently supported")


def make_response(data, status_code):
    raise NotImplementedError("Tornado is not currently supported")


class TornadoWebargsPlugin(WebargsPlugin, TornadoPlugin):
    def __init__(self):
        raise NotImplementedError("Tornado is not currently supported")

    def path_helper(self, operations, parameters, *, view, app=None, **kwargs):
        raise NotImplementedError("Tornado is not currently supported")

    def operation_helper(self, operations, *, view, **kwargs):
        raise NotImplementedError("Tornado is not currently supported")


WebargsPlugin = TornadoWebargsPlugin
