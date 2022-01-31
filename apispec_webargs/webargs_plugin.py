from typing import Union, Optional, List

from werkzeug import routing
from flask.views import MethodView
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from marshmallow import Schema
from webargs import fields, validate
from webargs.core import ArgMap
from webargs.flaskparser import parser

from . import MultipleOf

# def _generate_schema_from_field(field: fields.Field) -> dict:

#     def get_type_name(field: fields.Field) -> bool:
#         type_fields = (
#             ("number", (fields.Number,)),
#             ("boolean", (fields.Boolean,)),
#             ("object", (fields.Mapping, fields.Nested)),
#             ("string", (fields.String, fields.DateTime, fields.IP, fields.IPInterface, fields.Raw)),
#         )
#         for type_name, field_types in type_fields:
#             for field_type in field_types:
#                 if isinstance(field, field_type): return type_name
#         raise NotImplementedError(f"Field '{type(field)}' and superclasses not implemented!")

#     def get_format(field: Union[fields.String, fields.Number]) -> Optional[str]:
#         field_formats: dict[fields.Field, str] = {
#             fields.Date: "date",
#             fields.DateTime: "date-time",
#             fields.AwareDateTime: "date-time",
#             fields.NaiveDateTime: "date-time",
#             fields.Time: "date-time",
#             fields.Email: "email",
#             fields.IP: "ip",
#             fields.IPv4: "ipv4",
#             fields.IPv6: "ipv6",
#             fields.Url: "url",
#             fields.UUID: "uuid",
#             fields.Float: "float",
#         }
#         return field_formats.get(type(field))

#     schema_dict = {
#         # Test for Integer first because Integer is a subclass of Number
#         "type": "integer" if isinstance(field, fields.Integer) else get_type_name(field)
#     }

#     if isinstance(field, fields.String) or isinstance(field, fields.Number):
#         format = get_format(field)
#         if format:
#             schema_dict["format"] = format
    
#     if isinstance(field, fields.Number):
#         for validator in field.validators:
#             if isinstance(validator, validate.Range):
#                 schema_dict = {
#                     **schema_dict,
#                     "minimum": validator.min,
#                     "maximum": validator.max,
#                     "exclusiveMinimum": not validator.min_inclusive,
#                     "exclusiveMaximum": not validator.max_inclusive,
#                 }
#             if isinstance(validator, MultipleOf):
#                 schema_dict["multipleOf"] = validator.multiply

#     return schema_dict


# def _parse_dict_params(params: dict[str, fields.Field], location) -> dict:
#     out_dict = {}
#     if location == "query":
#         out_dict["parameters"] = []
#         for name, field in params.items():
#             new_param = {
#                 "in": location,
#                 "name": name,
#                 "schema": _generate_schema_from_field(field),
#                 "required": field.required,
#                 "description": field.metadata.get("description")
#             }


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


# def _parameters_data_from_rule(rule: routing.Rule) -> dict[str, list[dict]]:
def _parameters_data_from_rule(rule: routing.Rule) -> list[dict]:
    parameters: List[dict] = []
    for arg in rule.arguments:
        param_dict = {"name": arg, "in": "path", "required": True}
        param_dict["schema"] = _schema_data_from_converter(rule._converters[arg])
        parameters.append(param_dict)

    return parameters
    # return {"parameters": parameters} if parameters else {}


class WebargsFlaskPlugin(MarshmallowPlugin, FlaskPlugin):
    def __init__(self):
        super().__init__()
        self.rule_by_view = {}

    def path_helper(self, operations, parameters, *, view, app=None, **kwargs):
        rule = self.rule_by_view[view] = self._rule_for_view(view, app=app)
        # operations.update(_parameters_data_from_rule(rule))
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
                    # method_dict = {}
                    # arg_map: ArgMap = method.args_[0]
                    # if isinstance(arg_map, dict):
                    #     arg_map = parser.schema_class.from_dict(method.args_[0])()
                    #     method_dict = _parse_dict_params(method.args_[0])
                        # method_dict['parameters'] = [
                        #     {"name": name, "in": method.kwargs_["location"], **_generate_schema_from_field(field)}
                        #     for name, field in method.args_[0].items()
                        # ]
                        # for name, field in method.args_[0].items():
                            # _generate_schema_from_field(field)
                    operations.setdefault(method_name, {})
                    operations[method_name].update(
                        self._operation_data_from_argmap(method.args_[0], location=method.kwargs_["location"])
                    )
