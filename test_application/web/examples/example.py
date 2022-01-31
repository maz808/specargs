from flask.views import MethodView
from marshmallow import Schema
from webargs import fields

from apispec_webargs import use_kwargs


class Example(Schema):
    id = fields.Int()
    name = fields.Str()


class ExampleView(MethodView):
    @use_kwargs({"name": fields.Str()}, location = "query")
    def get(self, id, **kwargs):
        print(f"{id=}")
        print(kwargs)
        return 200