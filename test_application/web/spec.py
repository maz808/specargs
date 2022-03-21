from apispec_webargs import WebargsAPISpec, WebargsFlaskPlugin


spec = WebargsAPISpec(
    title="Test Spec",
    version="0.1.0",
    openapi_version="3.0.2",
    plugins=[WebargsFlaskPlugin()],
    servers=[{"url": "http://localhost:5000"}]
)
