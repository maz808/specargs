API
===

Spec/Plugin Objects
-------------------

.. autoclass:: specargs.WebargsAPISpec
   :members:
   :show-inheritance:
   :undoc-members:

.. autoclass:: specargs.WebargsPlugin
   :special-members:

View Function/Method Decorators
-------------------------------

.. autofunction:: specargs.use_args

.. autofunction:: specargs.use_kwargs

.. autofunction:: specargs.use_response

.. autofunction:: specargs.use_empty_response

Schema Inheritance/Polymorphism
-------------------------------

.. autoclass:: specargs.in_poly.InPoly
   :members:
   :exclude-members: keyword

.. autoclass:: specargs.OneOf
   :members:
   :member-order: bysource
   :show-inheritance:
   :special-members:

.. autoclass:: specargs.AnyOf
   :members:
   :show-inheritance:
   :special-members:

.. autoclass:: specargs.AllOf
   :members:
   :show-inheritance:
   :special-members:

Reusable Components
-------------------

.. autoclass:: specargs.Response
   :members:

Exceptions
----------

.. autoexception:: specargs.decorators.DuplicateResponseCodeError
   :special-members:

.. automodule:: specargs.in_poly
   :members:
   :exclude-members: InPoly, OneOf, AnyOf, AllOf

.. .. automodule:: specargs
..    :members:
..    :imported-members:
..    :exclude-members: WebargsPlugin, WebargsAPISpec, Response
..    :show-inheritance:
..    :special-members:
