from apispec import APISpec
from apispec_webargs.webargs_plugin import WebargsFlaskPlugin


spec = APISpec(
    title="Test Spec",
    version="0.1.0",
    openapi_version="3.0.2",
    plugins=[WebargsFlaskPlugin()]
    # plugins=[MarshmallowPlugin(), FlaskPlugin()]
)
