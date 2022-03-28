from apispec_webframeworks.bottle import BottlePlugin
from webargs.bottleparser import parser

from ..plugin import WebargsPlugin


def get_request_body(request):
    raise NotImplementedError("Bottle is not currently supported")


def create_paths(self, framework_obj):
    raise NotImplementedError("Bottle is not currently supported")


def make_response(data, status_code):
    raise NotImplementedError("Bottle is not currently supported")


class BottleWebargsPlugin(WebargsPlugin, BottlePlugin):
    def __init__(self):
        raise NotImplementedError("Bottle is not currently supported")

    def path_helper(self, operations, parameters, *, view, app=None, **kwargs):
        raise NotImplementedError("Bottle is not currently supported")

    def operation_helper(self, operations, *, view, **kwargs):
        raise NotImplementedError("Bottle is not currently supported")


WebargsPlugin = BottleWebargsPlugin
