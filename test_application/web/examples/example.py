from typing import Optional

import attr
from flask.views import MethodView
from marshmallow import Schema
from webargs import fields

from apispec_webargs import use_kwargs, response

from ..spec import spec


@attr.s(auto_attribs=True)
class Example:
    id: int
    name: str
    sub: Optional["Example"] = None


class ExampleSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    sub = fields.Nested("ExampleSchema")


spec.components.schema("OtherExample", schema=ExampleSchema)


class ExampleView(MethodView):
    @use_kwargs({"name": fields.Str()}, location = "query")
    @response(ExampleSchema)
    @response(ExampleSchema)
    def get(self, id, **kwargs):
        print(f"{id=}")
        print(kwargs)
        return 200
