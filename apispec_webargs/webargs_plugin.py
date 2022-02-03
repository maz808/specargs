import math
from typing import Union, List

from werkzeug import routing
from flask.views import MethodView
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from marshmallow import Schema
from webargs.core import ArgMap
from webargs.flaskparser import parser

from . import MultipleOf


def _schema_data_from_converter(converter: routing.BaseConverter) -> dict[str, Union[str, int, List[str]]]:
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


def _parameters_data_from_rule(rule: routing.Rule) -> list[dict]:
    parameters: List[dict] = []
    for arg in rule.arguments:
        param_dict = {"name": arg, "in": "path", "required": True}
        param_dict["schema"] = _schema_data_from_converter(rule._converters[arg])
        parameters.append(param_dict)

    return parameters


def field2multipleOf(self, field, **kwargs):
    """Return the dictionary of OpenAPI field attributes for a set of
    :class:`MultipleOf <apispec_webargs.MultipleOf>` validators.

    :param Field field: A marshmallow field.
    :rtype: dict
    """
    validators = [
        validator
        for validator in field.validators
        if isinstance(validator, MultipleOf)
    ]
    # Remove any validators that contain a value that is a factor of any of the other validator values
    validators = [
        validator for validator in validators for other_validator in validators
        if not any(other_validator.multiply % validator.multiply == 0)
    ]
    return {"multipleOf": math.prod(validator.multiply for validator in validators)}


class WebargsFlaskPlugin(MarshmallowPlugin, FlaskPlugin):
    def __init__(self):
        super().__init__()
        self.rule_by_view = {}
        self.converter.add_attribute_function(field2multipleOf)

    def path_helper(self, operations, parameters, *, view, app=None, **kwargs):
        rule = self.rule_by_view[view] = self._rule_for_view(view, app=app)
        parameters.extend(_parameters_data_from_rule(rule))
        return super().path_helper(operations={}, view=view, app=app, **kwargs)

    def _operation_data_from_schema(self, schema: Schema, *, location: str):
        return (self.converter.schema2jsonschema(schema) if location == "json" else
            {"parameters": self.converter.schema2parameters(schema, location=location)})

    def _operation_data_from_argmap(self, argmap: ArgMap, *, location: str):
        if isinstance(argmap, dict):
            argmap = parser.schema_class.from_dict(argmap)()
        return self._operation_data_from_schema(argmap, location=location)

    def operation_helper(self, operations, *, view, app=None, **kwargs):
        """Path helper that allows passing a Flask view function."""
        rule = self.rule_by_view[view]
        if hasattr(view, "view_class") and issubclass(view.view_class, MethodView):
            for method in view.methods:
                if method in rule.methods:
                    method_name = method.lower()
                    method = getattr(view.view_class, method_name)
                    operations.setdefault(method_name, {})
                    operations[method_name].update(
                        self._operation_data_from_argmap(method.args_[0], location=method.kwargs_["location"])
                    )
