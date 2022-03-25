from http import HTTPStatus

from flask import Blueprint
from flask.views import MethodView
from marshmallow import Schema
from webargs import fields, validate

from specargs import use_response, use_kwargs, use_empty_response, AllOf, AnyOf, OneOf

from .example import ExampleView, ExampleSchema, OtherSchema, Example
from ..spec import spec


@spec.schema
class ExamplesSchema(Schema):
    examples = fields.List(fields.Nested(ExampleSchema))


# examples_response = Response(ExamplesSchema, description="A response with example objects")
# spec.components.response("ExamplesResponse", response=examples_response)
examples_response = spec.response("ExamplesResponse", ExamplesSchema, description="A response with example objects")

class ExamplesView(MethodView):
    @use_kwargs({"startsWith": fields.String(), "count": fields.Integer(validate=validate.Range(min=1, max=5))}, location = "query")
    # @use_response(ExamplesSchema)
    @use_response(examples_response)
    def get(self, **kwargs):
        return {"examples": [Example(1, "Joe")]}

    @use_kwargs({"test": fields.String()}, location = "query")
    @use_kwargs(OneOf(ExampleSchema, OtherSchema, {"name": fields.String(), "test": fields.String()}))
    # @use_empty_response(status_code=HTTPStatus.CREATED)
    @use_response({"name": fields.String()})
    def post(self, **kwargs):
        print(kwargs)


examples_blueprint = Blueprint("examples-api", __name__, url_prefix="/examples")
examples_blueprint.add_url_rule("", view_func=ExamplesView.as_view("examples"))
examples_blueprint.add_url_rule("/<int(min=1, max=2):id>", view_func=ExampleView.as_view("example"))
