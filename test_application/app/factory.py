from specargs import use_kwargs
from flask_cors import CORS
from webargs import fields

from .app import App
from web import api_blueprints, spec

def create_app() -> App:
    app = App(__name__, static_folder=None)
    CORS(app)

    for blueprint in api_blueprints:
        app.register_blueprint(blueprint, url_prefix=f"/api{blueprint.url_prefix}")

    spec.create_paths(app)

    with open("./out_spec.yaml", "w") as fo:
        fo.write(spec.to_yaml())

    return app
