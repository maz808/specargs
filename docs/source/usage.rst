Usage
=====

Generating Specifications
-------------------------

Generating a specification is accomplished similarly to apispec. A :class:`~apispec_webargs.apispec.WebargsAPISpec` must
be instantiated and provided an instance of :class:`~apispec_webargs.webargs_plugin.WebargsFlaskPlugin` using the
`plugins` keyword argument. The methods of this :class:`~apispec_webargs.apispec.WebargsAPISpec` instance can then be
passed decorated Flask views and apispec-webargs objects which will be used to automatically generate an OpenAPI spec
with 
