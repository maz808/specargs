from apispec_webargs import use_kwargs
from webargs import fields

from .app import App
from web import api_blueprints, spec

def create_app() -> App:
    app = App(__name__)
    for blueprint in api_blueprints:
        app.register_blueprint(blueprint, url_prefix=f"/api{blueprint.url_prefix}")

    @app.get("/about")
    @use_kwargs({"details": fields.Bool()})
    def get_about():
        return "THIS IS THE ABOUT"

    @app.post("/about")
    @use_kwargs({"details": fields.Str()})
    def post_about():
        return "ABOUT POSTED"

    with app.test_request_context():
        for endpoint, view_func in app.view_functions.items():
            if endpoint == "static": continue
            spec.path(view=view_func)

    with open("./out_spec.yaml", "w") as fo:
        fo.write(spec.to_yaml())

    return app
