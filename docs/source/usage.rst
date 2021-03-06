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

Generating a specification is accomplished similarly to :doc:`apispec<apispec:index>`. A :class:`~specargs.WebargsAPISpec` must
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

When a `framework_obj` is passed to the :meth:`~specargs.WebargsAPISpec.create_paths` method, view functions/methods and
their corresponding url routing rules are extracted from ths object. These url rules are then converted into path parameter metadata for
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
functions/methods. This metadata can then be used by an instance of :class:`~specargs.WebargsAPISpec` to generate parameter metadata
in the resulting OpenAPI specification. These decorators can be used as shown below:

.. code-block:: python
    :caption: Flask example

    from flask import Flask
    from specargs import use_args
    from webargs import fields

    app = Flask(__name__, static_folder=None)

    @app.post("/users")
    @use_args({"name": fields.String(), "age": fields.Integer()}) # Must come after Flask decorator
    def post_user(args):
        print(args["name"])
        ...

    # If using class-based views, methods can be decorated instead
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
    :caption: Flask example

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
    :caption: Flask example

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
    :caption: Flask example

    @dataclass
    class User:
        id: int
        name: str
        age: int


    @app.get("/users/<int:user_id>")
    @use_response(
        {"id": fields.Integer(), "name": fields.String(), "age": fields.Integer()},
        description="The requested user",  # Default description is an empty string
    )
    def get_user(user_id: int):
        ...


    @app.post("/users")
    @use_kwargs({"name": fields.String(), "age": fields.Integer()})
    @use_response(
        fields.String,  # Can also be provided as `fields.String(kwargs**)` if using non-default kwargs
        status_code=HTTPStatus.CREATED,  # Default status_code is HTTPStatus.OK (200)
    )
    def post_user(name: str, age: int):
        ...

This will result in the following OAS structure:

.. code-block:: yaml

    paths:
      /users:
        post:
          responses:
            201:
              description: ""
              content: 
                text/html:
                  schema:
                    type: string
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

Aside from :mod:`marshmallow.fields` and dictionaries of :mod:`marshmallow.fields` as shown in the example above,
:func:`~specargs.use_response` can also accept a :class:`marshmallow.Schema` class or instance (:ref:`Schemas`), a
:class:`specargs.in_poly.InPoly` object (:ref:`Schema Inheritance and Polymorphism`), or a
:class:`specargs.Response` (:ref:`Responses`) as its first argument. This argument determines the contents
of the `content` block in the generated OAS structure.

Adding Empty Responses
----------------------

**specargs** also provides the convenience decorator :func:`~specargs.use_empty_response` for cases like an empty 404
response:

.. code-block:: python
    :caption: Flask example

    @app.get("/users/<int:user_id>")
    @use_empty_response(status_code=HTTPStatus.NOT_FOUND, description="The requested user was not found")
    def get_user(user_id: int):
        if user_id == NON_EXISTENT_USER_ID:
            abort(404)
        return User(id=user_id, name="Joe", age=24)

This would result in the same OAS output as if :func:`~specargs.use_response` were provided an empty dictionary or
`None` as the first argument:

.. code-block:: yaml

    paths:
      /users/{user_id}:
        parameters:
          - in: path
            name: user_id
            required: true
            type: integer
        get:
          responses:
            400:
              description: The requested user was not found

Response Data Serialization
---------------------------

While :func:`~specargs.use_args` and :func:`~specargs.use_kwargs` provide request data parsing,
:func:`~specargs.use_response` provides response data serialization based on :doc:`marshmallow <marshmallow:index>`. In
the code example shown in :ref:`Adding Response Metadata`, a Flask view function returns a `User` object, but because
it's decorated with :func:`~specargs.use_response`, the `User` object is serialized into a dictionary and placed into a
tuple, which is an acceptable return value for Flask. The underlying implementation of this serialization is dynamic so
that the serialized output is in a form that's appropriate for the current :ref:`Active Framework`.

.. note::

  :func:`~specargs.use_empty_response` will not serialize view function/method return data as no serialization schema is
  provided.

Adding Extra Responses with Content
-----------------------------------

There may be times when a view function/method may need to explicitly return more than one kind of response with
differing content and status codes. In this case, the view function/method can be decorated with multiple
:func:`~specargs.use_response` decorators, but as mentioned in :ref:`Response Data Serialization`, this would affect
the serialization of the return value depending on which response schema is used:

.. code-block:: python
    :caption: Flask example

    @app.post("/users/{user_id}")
    @use_response(
        {"id": fields.Integer(), "name": fields.String(), "age": fields.Integer()},
        description="The requested user"
    )
    @use_response(
        fields.String(),
        description="The requested user was not found",
        status_code=HTTPStatus.NOT_FOUND
    )
    def get_user(user_id: int):
        if user_id == NON_EXISTENT_USER_ID:
            # Needs to be handled by the second `use_response` above
            return "The requested user was not found!", HTTPStatus.NOT_FOUND
        # Should be handled by the first `use_response` above
        return User(id=user_id, name="Joe", age=24)

By default, the return data of a view function/method will be processed by the topmost decorator. In the example above,
this means the first :func:`~specargs.use_response` decorator would be used to serialize the data from both of the
return statements. In order to specify which decorator should process the return data, **specargs** provides the
:class:`~specargs.ViewResponse` class. The :class:`~specargs.ViewResponse` constructor accepts the return data as its first
argument and the intended response status as its second argument. The return data will then be processed by whichever
decorator has a matching `status_code`:

.. code-block:: python
    :caption: Flask example

    from specargs import use_response, use_empty_response, ViewResponse

    @app.post("/users/{user_id}")
    @use_response(
        {"id": fields.Integer(), "name": fields.String(), "age": fields.Integer()},
        description="The requested user"
    )
    @use_response(
        fields.String(),
        description="The requested user was not found",
        status_code=HTTPStatus.NOT_FOUND
    )
    def get_user(user_id: int):
        if user_id == NON_EXISTENT_USER_ID:
            # Will now be handled by the second `use_response` decorator
            return ViewResponse("The requested user was not found!", HTTPStatus.ACCEPTED)
        # Will still be handled by the default first `use_response` decorator
        return User(id=user_id, name="Joe", age=24)

Reusable Components
-------------------

In OAS, certian objects (schemas, responses, etc.) are able to be defined in the top level `components` section of an
OAS file. These defined components can then be referenced within other parts of the file to avoid repetition.
**specargs** provides means to do the same within code.

Schemas
*******

:doc:`marshmallow<marshmallow:index>` provides an analog to OAS schema objects wwith their :class:`~marshmallow.Schema`
class. :doc:`marshmallow<marshmallow:index>` :class:`~marshmallow.Schema` objects are accepted by both
:func:`~specargs.use_args` and :func:`~specargs.use_kwargs`, just like in :doc:`webargs<webargs:index>`. However, simply
defining and using them in those decorators won't add them to the `components` section of the generated OAS file. In
order to properly register a reusable schema in the OAS file, the corresponding :class:`~marshmallow.Schema` must be
provided to the :meth:`~specargs.WebargsAPISpec.schema` method of the :class:`specargs.WebargsAPISpec` class. After
being defined, a :class:`~marshmallow.Schema` class or instance can be provided :func:`~specargs.use_args`,
:func:`~specargs.use_kwargs`, or :func:`~specargs.use_response` which will provide request parsing and response data
serialization for the decorated view function/method.

.. code-block:: python
    :caption: Flask example

    from marshmallow import Schema, fields, validate
    from specargs import WebargsAPISpec

    spec = WebargsAPISpec(...)


    @spec.schema
    class NewUserSchema(Schema):
        name = fields.String(required=True)
        age = fields.Integer(validator=validate.Range(min=1, max=200))


    @spec.schema("User")
    class ExistingUserSchema(Schema):
        id = fields.Integer(required=True)
        name = fields.String(required=True)
        age = fields.Integer(validator=validate.Range(min=1, max=200))


    @dataclass
    class User:
        id: int
        name: str
        age: int


    @app.post("/users")
    @use_kwargs(NewUserSchema)
    @use_response(ExistingUserSchema, description="The newly created user", status_code=HTTPStatus.CREATED)
    def post_user(name: str, age: int):
        return User(1, "Joe", 25)

The above code will result in the following OAS output:

.. code-block:: yaml

    components:
      schemas:
        NewUser:
          type: object
          properties:
            name:
              type: string
            age:
              type: integer
              minimum: 1
              maximum: 200
          required:
            - name
        User:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            age:
              type: integer
              minimum: 1
              maximum: 200
          required:
            - id
            - name
    paths:
      /users:
        post:
          requestBody:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/NewUser'
            required: true
          responses:
            '201':
              description: The newly created user
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/User'

Responses
*********

**specargs** provides the :class:`~specargs.Response` class to generate reusable response components. Instead of
defining response metadata directly within the :func:`~specargs.use_response` decorator, this metatdata can be defined
within the :class:`~specargs.Response` constructor. The resulting :class:`~specargs.Response` object can then be
provided to multiple :func:`~specargs.use_response` decorators, reducing repetition when defining view functions/methods
with the same response metadata. However, instantiating a :class:`~specargs.Response` object with its constructor does
not automatically register it as a reusable response component. To accomplish this, the :class:`~specargs.Response`
instance can be provided to the :meth:`~specargs.WebargsAPISpec.response` method of the
:class:`~specargs.WebargsAPISpec` class, which will register a corresponding response object in the `components` section
of the generated OAS output:

.. code-block:: python

    from marshmallow import Schema, fields
    from specargs import WebargsAPISpec, Response

    spec = WebargsAPISpec(...)

    class UserSchema(Schema):
        id = fields.Integer()
        name = fields.String()
        age = fields.Integer()

    user_response = Response(UserSchema, description="A user")

    # The first argument is the desired name of the response object within the OAS output
    spec.response("UserResponse", user_response)

Alternatively, it's possible to combine the steps of construction and registration by using the
:meth:`specargs.WebargsAPISpec.response` method as a :class:`~specargs.Response` factory. After its first argument,
:meth:`~specargs.WebargsAPISpec.response` is able to accept any arguments and keyword arguments that would be provided to
the :class:`~specargs.Response` constructor:

.. code-block:: python

    # Importing 'Response' from 'specargs' is no longer needed
    user_response = spec.response("UserResponse", UserSchema, description="A user")

Once a :class:`~specargs.Response` object is created, it can then be provided to the :func:`~specargs.use_response`
decorator:

.. code-block:: python
    :caption: Flask example

    # After a `Response` object named `user_response` has been created

    @app.get("/users/<int:user_id>")
    @use_response(user_response)
    def get_user(user_id: int):
        ...

    @app.post("/users")
    @use_kwargs({"name": fields.String(), "age": fields.Integer()})
    @user_response(user_response, status_code=HTTPStatus.CREATED)
    def post_user(name: str, age: int):
        ...

The resulting OAS output would be:

.. code-block:: yaml

    components:
      schemas:
        User:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            age:
              type: integer
      responses:
        UserResponse:
          description: A user
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
    paths:
      /users:
        post:
          requestBody:
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    name:
                      type: string
                    age:
                      type: integer
            required: true
          responses:
            '201':
              $ref: '#/components/responses/UserResponse'
      /users/{user_id}:
        parameters:
          - in: path
            name: user_id
            required: true
            schema:
              type: integer
        get:
          respones:
            '200':
              $ref: '#/components/responses/UserResponse'

Schema Inheritance and Polymorphism
-----------------------------------

In OAS, schema inheritance and polymorphism is accomplished using the `oneOf`, `anyOf`, and `allOf` keywords. In order
to match the features of OAS, **specargs** provides the :class:`~specargs.OneOf`, :class:`~specargs.AnyOf`, and
:class:`~specargs.AllOf` classes which all inherit from the :class:`specargs.in_poly.InPoly` class. These classes can
be used in all **specargs** functions and methods where a dictionary of :mod:`marshmallow.fields` or a
:class:`marshmallow.Schema` class or instance can be provided. Before the explanation and examples of how each of these
:class:`~specargs.in_poly.InPoly` subclasses can be used, let the following dataclasses and schemas be defined:

.. code-block:: python

    from dataclass import dataclass
    from marshmallow import Schema, fields
    from specargs import WebargsAPISpec

    spec = WebargsAPISpec(...)

    @dataclass
    class Spoon:
        volume: float

    @dataclass
    class Fork:
        prongs: int

    @dataclass
    class Spork:
        volume: float
        prongs: int
    
    @dataclass
    class Knife:
        serrated: bool

    @spec.schema
    class SpoonSchema(Schema):
        volume = fields.Float()

    @spec.schema
    class ForkSchema(Schema):
        prongs = fields.Integer()

The schemas defined above will generate the following OAS components:

.. code-block:: yaml

    components:
      schemas:
        Spoon:
          type: object
          properties:
            volume:
              type: number
        Fork:
          type: object
          properties:
            prongs:
              type: integer

OneOf
*****

The :class:`~specargs.OneOf` class can be used to define request/response metadata with multiple object schemas, only
one of which should successfully validate the given data. The schemas can be provided as :class:`marshmallow.Schema`
classes or instances:

.. code-block:: python
    :caption: Flask example

    from specargs import use_args, use_response, use_empty_response, OneOf

    @app.post("/utensils")
    @use_args(OneOf(SpoonSchema(), ForkSchema))
    @use_empty_response(description="A new utensil was successfully posted", status_code=HTTPStatus.CREATED)
    def post_utensil(args: dict):
        # At this point we have a dictionary that either has the attributes of Spoon or the attributes of Fork
        # It may be useful to add `post_load` methods to both Schemas so that the resulting `args` object is a Fork or
        # Spoon instead of a dictionary
        ...

    @app.get("/utensils/<int:utensil_id>")
    @use_response(OneOf(SpoonSchema, ForkSchema()), description="The requested utensil")
    def get_utensil(utensil_id: int):
        ...  # Steps that lead to returning a Spoon
            return Spoon(volume=14.8)  # Valid against only SpoonSchema (CORRECT)
        ...  # Steps that lead to returning a Fork
            return Fork(prongs=3)  # Valid against only ForkSchema (CORRECT)
        ...  # Steps that lead to returning a Spork
            return Spork(volume=13.2, prongs=4)  # Valid against both schemas (ERROR)
        ...  # Steps that lead to returning a Knife
            return Knife(serrated=True)  # Valid against neither schema (ERROR)

When parsing request data or serializing response data, using :class:`~specargs.OneOf` will raise an error if the data
is valid for more than one of the provided schemas or if the data is invalid against all provided schemas. The above
code will result in the following OAS output:

.. code-block:: yaml

    paths:
      /utensils:
        post:
          requestBody:
            content:
              application/json:
                schema:
                  oneOf:
                    - $ref: '#/components/schemas/Spoon'
                    - $ref: '#/components/schemas/Fork'
          responses:
            '201':
              description: A new utensil was successfully posted
      /utensils/{utensil_id}:
        parameters:
          - in: path
            name: utensil_id
            required: true
            schema:
              type: integer
        get:
          responses:
            '200':
              description: The requested utensil
              content:
                application/json:
                  schema:
                    oneOf:
                      - $ref: '#/components/schemas/Spoon'
                      - $ref: '#/components/schemas/Fork'

AnyOf
*****

The :class:`~specargs.AnyOf` class can be used to define request/response metadata with multiple object schemas,
multiple of which could successfully validate the given data. The schemas can be provided as :class:`marshmallow.Schema`
classes or instances:

.. code-block:: python
    :caption: Flask example

    from specargs import use_args, use_response, use_empty_response, OneOf

    @app.post("/utensils")
    @use_args(AnyOf(SpoonSchema(), ForkSchema))
    @use_empty_response(description="A new utensil was successfully posted", status_code=HTTPStatus.CREATED)
    def post_utensil(args: dict):
        # At this point we have a dictionary that has either the attributes of Spoon, the attributes of Fork, or both
        # Schemas with `post_load` methods that return non-dictionary objects will still output a dictionary
        ...

    @app.get("/utensils/<int:utensil_id>")
    @use_response(AnyOf(SpoonSchema, ForkSchema()), description="The requested utensil")
    def get_utensil(utensil_id: int):
        ...  # Steps that lead to returning a Spoon
            return Spoon(volume=14.8)  # Valid against only SpoonSchema (CORRECT)
        ...  # Steps that lead to returning a Fork
            return Fork(prongs=3)  # Valid against only ForkSchema (CORRECT)
        ...  # Steps that lead to returning a Spork
            return Spork(volume=13.2, prongs=4)  # Valid against both schemas (CORRECT)
        ...  # Steps that lead to returning a Knife
            return Knife(serrated=True)  # Valid against neither schema (ERROR)

When parsing request data or serializing response data, using :class:`~specargs.AnyOf` will raise an error if the data
is invalid against all of the provided schemas. The above code will result in the following OAS output:

.. code-block:: yaml

    paths:
      /utensils:
        post:
          requestBody:
            content:
              application/json:
                schema:
                  anyOf:
                    - $ref: '#/components/schemas/Spoon'
                    - $ref: '#/components/schemas/Fork'
          responses:
            '201':
              description: A new utensil was successfully posted
      /utensils/{utensil_id}:
        parameters:
          - in: path
            name: utensil_id
            required: true
            schema:
              type: integer
        get:
          responses:
            '200':
              description: The requested utensil
              content:
                application/json:
                  schema:
                    anyOf:
                      - $ref: '#/components/schemas/Spoon'
                      - $ref: '#/components/schemas/Fork'

Using :class:`~specargs.AnyOf` for request parsing and response serialization will also raise an error if the provided
schemas result in differing values for any given key after parsing or serialization. For example, cases in which the
provided schemas contain fields with matching names but differing types will raise an error.

AllOf
*****

The :class:`~specargs.AllOf` class can be used to define request/response metadata with multiple object schemas, all of
which should successfully validate the given data. The schemas can be provided as :class:`marshmallow.Schema` classes or
instances:

.. code-block:: python
    :caption: Flask example

    from specargs import use_args, use_response, use_empty_response, OneOf

    @app.post("/utensils")
    @use_args(AllOf(SpoonSchema(), ForkSchema))
    @use_empty_response(description="A new utensil was successfully posted", status_code=HTTPStatus.CREATED)
    def post_utensil(args: dict):
        # At this point we have a dictionary that has the attributes of Spoon and the attributes of Fork
        # Schemas with `post_load` methods that return non-dictionary objects will still output a dictionary
        ...

    @app.get("/utensils/<int:utensil_id>")
    @use_response(AnyOf(SpoonSchema, ForkSchema()), description="The requested utensil")
    def get_utensil(utensil_id: int):
        ...  # Steps that lead to returning a Spoon
            return Spoon(volume=14.8)  # Valid against only SpoonSchema (ERROR)
        ...  # Steps that lead to returning a Fork
            return Fork(prongs=3)  # Valid against only ForkSchema (ERROR)
        ...  # Steps that lead to returning a Spork
            return Spork(volume=13.2, prongs=4)  # Valid against both schemas (CORRECT)
        ...  # Steps that lead to returning a Knife
            return Knife(serrated=True)  # Valid against neither schema (ERROR)

When parsing request data or serializing response data, using :class:`~specargs.AllOf` will raise an error if the data
is invalid against any of the provided schemas. The above code will result in the following OAS output:

.. code-block:: yaml

    paths:
      /utensils:
        post:
          requestBody:
            content:
              application/json:
                schema:
                  allOf:
                    - $ref: '#/components/schemas/Spoon'
                    - $ref: '#/components/schemas/Fork'
          responses:
            '201':
              description: A new utensil was successfully posted
      /utensils/{utensil_id}:
        parameters:
          - in: path
            name: utensil_id
            required: true
            schema:
              type: integer
        get:
          responses:
            '200':
              description: The requested utensil
              content:
                application/json:
                  schema:
                    allOf:
                      - $ref: '#/components/schemas/Spoon'
                      - $ref: '#/components/schemas/Fork'

Using :class:`~specargs.AllOf` for request parsing and response serialization will also raise an error if the provided
schemas result in differing values for any given key after parsing or serialization. For example, cases in which the
provided schemas contain fields with matching names but differing types will raise an error.

Generating an OAS File
----------------------

Once all components have been added to a :class:`~specargs.WebargsAPISpec` instance, an OAS definition can be
output using the :meth:`~specargs.WebargsAPISpec.to_dict` and :meth:`~specargs.WebargsAPISpec.to_yaml`
methods, exactly as with :class:`apispec.APISpec`.
