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

**specargs** checks the Python environment for the frameworks mentioned in :ref:`Supported Frameworks`. Usage of
**specargs** is dependent on which of these frameworks is installed in the current environment. If more than one
of these frameworks is detected, an error will be raised, as selection of a specific framework when multiple are present
is currently not supported. If only one is detected, that framework is set as the active framework.


Initializing a Specification
----------------------------

Generating a specification is accomplished similarly to apispec. A :class:`~specargs.WebargsAPISpec` must
be instantiated and provided an instance of :class:`~specargs.WebargsPlugin` using the `plugins`
keyword argument:

.. code-block:: python

    from specargs import WebargsAPISpec, WebargsPlugin

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

Adding paths with operations can be accomplished using the :meth:`~specargs.WebargsAPISpec.create_paths` method
of the :class:`~specargs.WebargsAPISpec` class. This method accepts one argument, `framework_obj`. The type of
object accepted for this argument is dependent on the current active framework (as mentioned in :ref:`Active
Framework`).  The frameworks and accepted objects are as follows:

- Flask: :class:`flask.Flask`

For example, paths and operations can be generated from a Flask application like so:

.. code-block:: python

    from flask import Flask
    from specargs import WebargsAPISpec, WebargsPlugin

    app = Flask(__name__, static_folder=None)
    spec = WebargsAPISpec(..., plugins=[WebargsPlugin()])

    ...
    # Register views to app
    ...

    spec.create_paths(app)

Adding Path Parameter Metadata
------------------------------

When a `framework_obj` is passed to the :meth:`~specargs.WebargsAPISpec.create_paths`, view functions/methods and
thier corresponding url routing rules are extracted. These url rules are then converted into path parameter metadata for
the generated paths of the output OpenAPI specification. Using Flask, for example:

.. code-block:: python

    @app.get("/users/<int:user_id>/pets/<pet_name>")
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

As **specargs** is intended to provide a thin wrapper around :doc:`webargs:index`, it also provides
:func:`~specargs.use_args` and :func:`~specargs.use_kwargs` decorator functions.  On top of the
functionality they provide in :doc:`webargs:index`, these decorators also attach metadata onto decorated view
functions/methods that's used by an instance of :class:`~specargs.WebargsAPISpec` to generate parameter metadata
in the resulting OpenAPI specification. These decorators can be used as shown below:

.. code-block:: python

    from flask import Flask
    from specargs import use_args
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

:func:`specargs.use_kwargs` is used the same way, but will pass in keyword arguments instead of a single
positional argument:

.. code-block:: python

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
                      type: integer

Adding Parameter Metadata to Operations
---------------------------------------

The same :meth:`specargs.use_args` and :meth:`specargs.use_kwargs` methods can be used to provide metadata
for parameters not accepted in the request body. For example:

.. code-block:: python

    @app.get("/users")
    @use_args({"name": fields.String()}, location="query")  # Default 'location' is the same as the webargs parser
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

Adding Response Metadata
------------------------

Building on :func:`~specargs.use_args` and :func:`~specargs.use_kwargs`, **specargs** provides another decorator
function :func:`~specargs.use_response`, which attaches response metadata to view functions/methods for use by an
instance of :class:`specargs.WebargsAPISpec`:

.. code-block:: python

    @dataclass
    class User:
        id: int
        name: str
        age: int


    @app.get("/users/<int:user_id>")
    @use_response(
        {"id": fields.Integer(), "name": fields.String(), "age": fields.Integer()},
        description="The requested user",
    )
    @use_response({}, status_code=HTTPStatus.NOT_FOUND)  # Default status_code is HTTPStatus.OK (200)
    def get_user(user_id: int):
        if user_id == NON_EXISTENT_USER_ID:
            abort(404)
        return User(id=user_id, name="Joe", age=24)

This will result in the following OAS structure:

.. code-block:: yaml

    paths:
      /users/{user_id}:
        parameters:
          - in: path
            name: user_id
            required: true
            schema:
              type: integer
        get:
          responses:
            200:
              description: The requested user
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      id:
                        schema:
                          type: integer
                      name:
                        schema:
                          type: string
                      age:
                        schema:
                          type: integer
            404:
              description: # The default description is an empty string

**specargs** also provides the convenience decorator :func:`~specargs.use_empty_response` for cases like the empty 404
response above:

.. code-block:: python

    @app.get("/users/<int:user_id>")
    @use_response(
        {"id": fields.Integer(), "name": fields.String(), "age": fields.Integer()},
        description="The requested user",
    )
    @use_empty_response(status_code=HTTPStatus.NOT_FOUND)  # An empty dictionary no longer needs to be povided
    def get_user(user_id: int):
        if user_id == NON_EXISTENT_USER_ID:
            abort(404)
        return User(id=user_id, name="Joe", age=24)

This would result in the same OAS output as if :func:`~specargs.use_response` were provided an empty dictionary.

Response Data Serialization
---------------------------

While :func:`~specargs.use_args` and :func:`~specargs.use_kwargs` provide request data parsing,
:func:`~specargs.use_response` provides response data serialization based on :doc:`marshmallow <marshmallow:index>`. In
the code example shown in :ref:`Adding Response Metadata`, a Flask view function returns a `User` object, but because
it's decorated with :func:`~specargs.use_response`, the `User` object is serialized into a dictionary and placed into a
tuple, which is an acceptable return value for Flask. The underlying implementation of this serialization is dynamic so
that the serialized output is in a form that's appropriate for the current :ref:`Active Framework`.

.. note::

  :func:`~specargs.use_empty_response` will not serialize view function/method return data as no serilization schema is
  provided.

Adding Extra Responses with Content
-----------------------------------

There may be times when a view function may need to explicitly return more than one kind of response with differing content and status codes.

Generating an OAS File
----------------------

Once all components have been added to a :class:`~specargs.WebargsAPISpec` instance, an OAS definition can be
output using the :meth:`~specargs.WebargsAPISpec.to_dict` and :meth:`~specargs.WebargsAPISpec.to_yaml`
methods, exactly as with :class:`apispec.APISpec`.
