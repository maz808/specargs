# TODO: Add support for Django
import json

from django.http import HttpRequest
from webargs.djangoparser import parser

from ..plugin import WebargsPlugin


def get_request_body(request: HttpRequest):
    return json.loads(request.body)


def create_paths(self, framework_obj):
    raise NotImplementedError("Django is currently not supported!")


def make_response(data, status_code):
    raise NotImplementedError("Django is currently not supported!")


class DjangoWebargsPlugin(WebargsPlugin):
    def __init__(self):
        raise NotImplementedError("Django is not currently supported")

    def path_helper(self, operations, parameters, *, view, app=None, **kwargs):
        raise NotImplementedError("Django is not currently supported")

    def operation_helper(self, operations, *, view, **kwargs):
        raise NotImplementedError("Django is not currently supported")


WebargsPlugin = DjangoWebargsPlugin
