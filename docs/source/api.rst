API
===

Spec/Plugin Objects
-------------------

.. autoclass:: apispec_webargs.WebargsAPISpec
   :members:
   :show-inheritance:
   :undoc-members:

.. autoclass:: apispec_webargs.WebargsPlugin
   :special-members:

View Function/Method Decorators
-------------------------------

.. autofunction:: apispec_webargs.use_args

.. autofunction:: apispec_webargs.use_kwargs

.. autofunction:: apispec_webargs.use_response

.. autofunction:: apispec_webargs.use_empty_response

Schema Inheritance/Polymorphism
-------------------------------

.. autoclass:: apispec_webargs.in_poly.InPoly
   :members:
   :exclude-members: keyword

.. autoclass:: apispec_webargs.OneOf
   :members:
   :member-order: bysource
   :show-inheritance:
   :special-members:

.. autoclass:: apispec_webargs.AnyOf
   :members:
   :show-inheritance:
   :special-members:

.. autoclass:: apispec_webargs.AllOf
   :members:
   :show-inheritance:
   :special-members:

Reusable Components
-------------------

.. autoclass:: apispec_webargs.Response
   :members:

Exceptions
----------

.. autoexception:: apispec_webargs.decorators.DuplicateResponseCodeError
   :special-members:

.. automodule:: apispec_webargs.in_poly
   :members:
   :exclude-members: InPoly, OneOf, AnyOf, AllOf

.. .. automodule:: apispec_webargs
..    :members:
..    :imported-members:
..    :exclude-members: WebargsPlugin, WebargsAPISpec, Response
..    :show-inheritance:
..    :special-members:
