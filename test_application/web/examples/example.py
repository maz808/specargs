from typing import Optional

import attr
from flask.views import MethodView
from marshmallow import Schema
from webargs import fields

from apispec_webargs import use_kwargs, response, AnyOf

from ..spec import spec


@attr.s(auto_attribs=True)
class Example:
    id: int
    name: str
    req: str = "nice"
    other_req: str = "other nice"
    # another_req: str = "another nice"
    sub: Optional["Example"] = None
    test: str = "wow"


class ExampleSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    sub = fields.Nested("ExampleSchema", allow_none=True)
    req = fields.String(required=True)


spec.components.schema("Example", schema=ExampleSchema)


class OtherSchema(Schema):
    id = fields.Int()
    name = fields.String()
    test = fields.Str()
    other_req = fields.Str(required=True)


spec.components.schema("Other", schema=OtherSchema)


class AnotherOneSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    another_req = fields.String(required=True)


spec.components.schema("AnotherOne", schema=AnotherOneSchema)


class ExampleView(MethodView):
    @use_kwargs({"name": fields.Str()}, location = "query")
    @response(AnyOf(ExampleSchema, OtherSchema))
    def get(self, id, **kwargs):
        return Example(id=id, name=kwargs.get("name") or "example")

