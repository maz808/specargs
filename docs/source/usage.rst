Usage
=====

Supported Frameworks
--------------------

The supported frameworks currently include:

- Flask

There are plans to support the following frameworks:

- Django
- Tornado
- Bottle
- :doc:`Other frameworks <webargs:framework_support>` supported by :doc:`webargs <webargs:index>`

Active Framework
----------------

**apispec-webargs** checks the Python environment for the frameworks mentioned in :ref:`Supported Frameworks`. Usage of
**apispec-webargs** is dependent on which of these frameworks is installed in the current environment. If more than one
of these frameworks is detected, an error will be raised, as selection of a specific framework when multiple are present
is currently not supported. If only one is detected, that framework is set as the active framework.


Initializing a Specification
----------------------------

Generating a specification is accomplished similarly to apispec. A :class:`~apispec_webargs.WebargsAPISpec` must
be instantiated and provided an instance of :class:`~apispec_webargs.WebargsPlugin` using the `plugins`
keyword argument::

    from apispec_webargs import WebargsAPISpec, WebargsPlugin

    spec = WebargsAPISpec(
        title="Example API Spec",
        version="1.0.0",
        openapi_version="3.0.2",
        plugins=[WebargsPlugin()],
        servers=[
            {"url": "http://localhost:5000"}, # If testing locally
            {"url": "http://dev-server-url"}
        ]
    )

Adding Paths and Operations
---------------------------

Adding paths with operations can be accomplished using the :meth:`~apispec_webargs.WebargsAPISpec.create_paths` method
of the :class:`~apispec_webargs.WebargsAPISpec` class. This method accepts one argument, `framework_obj`. The type of
object accepted for this argument is dependent on the current active framework (as mentioned in :ref:`Active
Framework`).  The frameworks and accepted objects are as follows:

- Flask: :class:`flask.Flask`

For example, paths and operations can be generated from a Flask application like so::

    from flask import Flask
    from apispec_webargs import WebargsAPISpec, WebargsPlugin

    app = Flask(__name__, static_folder=None)
    spec = WebargsAPISpec(..., plugins=[WebargsPlugin()])

    ...
    # Register views to app
    ...

    spec.create_paths(app)

Adding Path Parameter Metadata
------------------------------

When a `framework_obj` is passed to the :meth:`~apispec_webargs.WebargsAPISpec.create_paths`, view functions/methods and
thier corresponding url routing rules are extracted. These url rules are then converted into path parameter metadata for
the generated paths of the output OpenAPI specification. Using Flask, for example::

    @app.get(/users/<int:user_id>/pets/<pet_name>)
    def get_user_pet_by_name(user_id: int, pet_name: str):
        ...

    spec.create_paths(app)

The above code will result in the following OpenAPI path object:

.. code-block:: yaml

    paths:
      /users/{user_id}/pets/{pet_name}:
        parameters:
          - in: path
            name: user_id
            required: true
            schema:
              type: integer
          - in: path
            name: pet_name
            required: true
            schema:
              type: string

Adding Request Body Metadata to Operations
------------------------------------------

As **apispec-webargs** is intended to provide a thin wrapper around :doc:`webargs:index`, it also provides
:func:`~apispec_webargs.use_args` and :func:`~apispec_webargs.use_kwargs` decorator functions.  On top of the
functionality they provide in :doc:`webargs:index`, these decorators also attach metadata onto decorated view
functions/methods that's used by an instance of :class:`~apispec_webargs.WebargsAPISpec` to generate parameter metadata
in the resulting OpenAPI specification. These decorators can be used as shown below::

    from flask import Flask
    from apispec_webargs import use_args
    from webargs import fields

    app = Flask(__name__, static_folder=None)

    @app.post("/users")
    @use_args({"name": fields.String(), "age"}) # Must come after Flask decorator
    def post_user(args):
        print(args["name"])
        ...

    # If using class-based views, you can decorated view methods instead
    from flask.view import MethodView

    class Users(MethodView):
        @use_args({"name": fields.String(required=True), "age": fields.Integer()})
        def post(args):
            print(args["name"])
            print(args.get("age"))
            ...

:func:`apispec_webargs.use_kwargs` is used the same way, but will pass in keyword arguments instead of a single
positional argument::

    @app.post("/users")
    @use_kwargs({"name": fields.String(required=True), "age": fields.Integer()})
    def post_user(name: str, age: int = None):
        print(name)
        print(age)
        ...

The above code snippets will all result in the same OpenAPI structure:

.. code-block:: yaml

    paths:
      /users:
        get:
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  type: object
                  required:
                    - name
                  properties:
                    name:
                      type: string
                    age:
                      type: int

Adding Parameter Metadata to Operations
---------------------------------------

The same :meth:`apispec_webargs.use_args` and :meth:`apispec_webargs.use_kwargs` methods can be used to provide metadata
for parameters not accepted in the request body. For example::

    @app.get("/users")
    @use_args({"name": fields.String()}, location="query") # Default 'location' is the same as the webargs parser
    def get_users(args):
        print(args["name"])
        ...

The above code snippet will result in this OpenAPI structure:

.. code-block:: yaml

    paths:
      /users:
        get:
          parameters:
            - in: query
              name: name
              required: false
              schema:
                type: string

Adding Response Metadata/Serialization
--------------------------------------

Building on :func:`~apispec_webargs.use_args` and :func:`~apispec_webargs.use_kwargs`, **apispec-webargs** provides
another decorator function :func:`~apispec_webargs.use_response`. This function is also used as view function/method
decorator.

Generating an OAS File
----------------------

Once all components have been added to a :class:`~apispec_webargs.WebargsAPISpec` instance, an OAS definition can be
output using the :meth:`~apispec_webargs.WebargsAPISpec.to_dict` and :meth:`~apispec_webargs.WebargsAPISpec.to_yaml`
methods, exactly as with :class:`apispec.APISpec`.
