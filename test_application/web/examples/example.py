from typing import Optional

from attrs import define
from flask.views import MethodView
from marshmallow import Schema
from webargs import fields

from apispec_webargs import use_response, use_kwargs, AnyOf

from ..spec import spec


@define
class Example:
    id: int
    name: str
    req: str = "nice"
    # other_req: str = "other nice"
    # another_req: str = "another nice"
    # sub: Optional["Example"] = None
    # test: str = "wow"


@spec.schema("Example")
class ExampleSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    sub = fields.Nested("ExampleSchema", allow_none=True)
    req = fields.String(required=True)


@spec.schema("Other")
class OtherSchema(Schema):
    id = fields.Int()
    name = fields.String()
    test = fields.Str()
    other_req = fields.Str(required=True)


@spec.schema("AnotherOneButWithAWeirdName")
class AnotherOneSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    another_req = fields.String(required=True)


class ExampleView(MethodView):
    @use_kwargs({"name": fields.Str()}, location = "query")
    @use_response(AnyOf(ExampleSchema, OtherSchema))
    def get(self, id, **kwargs):
        return Example(id=id, name=kwargs.get("name") or "example")
