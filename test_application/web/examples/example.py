from http import HTTPStatus
from typing import Optional

from attrs import define
from flask import abort
from flask.views import MethodView
from marshmallow import Schema, post_load
from webargs import fields

from specargs import use_response, use_kwargs, AnyOf, use_empty_response, Response

from ..spec import spec


@define
class Example:
    id: int
    req: str
    name: str = "name"
    # other_req: str = "other nice"
    # another_req: str = "another nice"
    # sub: Optional["Example"] = None
    # test: str = "wow"


@define
class Other:
    id: int
    other_req: str
    name: str = "name"
    test: str = "test"


@spec.schema("Example")
class ExampleSchema(Schema):
    id = fields.Int(required=True)
    req = fields.String(required=True)
    name = fields.Str()

    @post_load
    def make_example(self, data, **kwargs):
        return Example(**data)


@spec.schema("Other")
class OtherSchema(Schema):
    id = fields.Int()
    name = fields.String()
    test = fields.Str()
    other_req = fields.Str(required=True)

    @post_load
    def make_other(self, data, **kwargs):
        return Other(**data)


@spec.schema("AnotherOneButWithAWeirdName")
class AnotherOneSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    another_req = fields.String(required=True)


class ExampleView(MethodView):
    @use_kwargs({"name": fields.Str()}, location = "query")
    @use_response(AnyOf(ExampleSchema, OtherSchema))
    @use_empty_response(status_code=HTTPStatus.NOT_FOUND, description="The example with the given id was not found")
    def get(self, id, **kwargs):
        if id == 8:
            abort(404)
        return Response(Example(id=id, name=kwargs.get("name") or "example"), HTTPStatus.OK)
