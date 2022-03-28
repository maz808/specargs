from typing import Dict, List, Union

from apispec_webframeworks.flask import FlaskPlugin
from werkzeug import routing
from webargs.flaskparser import parser

from flask import Request, Flask
from flask.views import MethodView

from ..plugin import WebargsPlugin


def get_request_body(request: Request):
    return request.json


def create_paths(self, framework_obj: Flask):
    if not isinstance(framework_obj, Flask):
        raise TypeError("The provided object is not of type `flask.Flask`!")

    for view_func in framework_obj.view_functions.values():
        self.path(view=view_func, app=framework_obj)


def make_response(data, status_code):
    return data, status_code


def _schema_data_from_converter(converter: routing.BaseConverter) -> Dict[str, Union[str, int, List[str]]]:
    if isinstance(converter, routing.UnicodeConverter):
        param_type = "string"
        length_args = converter.regex[converter.regex.index("{") + 1, converter.regex.index("}")].split(",")
        minLength = int(length_args[0])
        maxLength = minLength if len(length_args) == 1 else length_args[1]
        schema_dict = {"minLength": minLength}
        if maxLength:
            maxLength = int(maxLength)
            schema_dict["maxLength"] = maxLength
    elif isinstance(converter, routing.PathConverter):
        param_type = "string"
        schema_dict = {"format": "url", "pattern": converter.regex}
    elif isinstance(converter, routing.NumberConverter):
        param_type = "integer" if isinstance(converter, routing.IntegerConverter) else "number"
        minimum = converter.min
        if not converter.signed: minimum = max(minimum or 0, 0)
        schema_dict = {}
        if minimum: schema_dict["minimum"] = minimum
        if converter.max: schema_dict["maximum"] = converter.max
    elif isinstance(converter, routing.UUIDConverter):
        param_type = "string"
        schema_dict = {"fomat": "uuid", "pattern": converter.regex}
    elif isinstance(converter, routing.AnyConverter):
        param_type = "string"
        values = converter.regex[converter.regex.index(":") + 1, -1].split("|")
        schema_dict = {"enum": values}
    else:
        raise NotImplementedError("Custom routing converters are not currently supported!")

    return {"type": param_type, **schema_dict}


def _parameters_data_from_rule(rule: routing.Rule) -> List[dict]:
    parameters: List[dict] = []
    for arg in rule.arguments:
        param_dict = {"name": arg, "in": "path", "required": True}
        param_dict["schema"] = _schema_data_from_converter(rule._converters[arg])
        parameters.append(param_dict)

    return parameters


class FlaskWebargsPlugin(WebargsPlugin, FlaskPlugin):
    def __init__(self):
        super().__init__()
        self.rule_by_view = {}

    def path_helper(self, operations, parameters, *, view, app=None, **kwargs):
        rule = self.rule_by_view[view] = self._rule_for_view(view, app=app)
        parameters.extend(_parameters_data_from_rule(rule))
        # An empty dict is passed into the operations argument to circumvent FlaskPlugin's operations changes
        return super().path_helper(operations={}, view=view, app=app, **kwargs)

    def operation_helper(self, operations, *, view, **kwargs):
        """Path helper that allows passing a view function."""
        rule = self.rule_by_view[view]
        if hasattr(view, "view_class") and issubclass(view.view_class, MethodView):
            for method in view.methods:
                # Check if method was registered in view but not in rule
                if method not in rule.methods: continue
                method_name = method.lower()
                method = getattr(view.view_class, method_name)
                self._update_operations(operations, view=method, method_name=method_name)
        else:
            for method in rule.methods:
                if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}: continue
                method_name = method.lower()
                self._update_operations(operations, view=view, method_name=method_name)


WebargsPlugin = FlaskWebargsPlugin
