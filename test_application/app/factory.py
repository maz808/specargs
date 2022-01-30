from .app import App
from web import api_blueprints

def create_app() -> App:
    app = App(__name__)
    for blueprint in api_blueprints:
        app.register_blueprint(blueprint, url_prefix=f"/api{blueprint.url_prefix}")

    return app
