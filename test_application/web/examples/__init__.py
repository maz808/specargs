from flask import Blueprint
from flask.views import MethodView
from webargs import fields, validate

from apispec_webargs import use_kwargs

from .example import ExampleView, Example


class ExamplesView(MethodView):
    @use_kwargs({"startsWith": fields.String(), "count": fields.Integer(validate=validate.Range(min=1, max=5))}, location = "query")
    def get(self, **kwargs):
        print(kwargs)
        return "EXAMPLES!"


examples_blueprint = Blueprint("examples-api", __name__, url_prefix="/examples")
examples_blueprint.add_url_rule("", view_func=ExamplesView.as_view("examples"))
examples_blueprint.add_url_rule("/<int(min=1, max=2):id>", view_func=ExampleView.as_view("example"))
