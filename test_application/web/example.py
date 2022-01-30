from flask import Blueprint
from flask.views import MethodView
from marshmallow import Schema
from webargs import fields
from webargs.flaskparser import use_kwargs


class Example(Schema):
    pass

class ExampleView(MethodView):
    @use_kwargs({"name": fields.Str()})
    def get(**kwargs):
        print(kwargs["name"])
        return "EXAMPLE!"


example_blueprint = Blueprint("example", __name__, url_prefix="/example")
example_blueprint.add_url_rule("", view_func=ExampleView.as_view("example"))
