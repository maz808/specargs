API
===

Spec/Plugin Objects
-------------------

.. autoclass:: specargs.WebargsAPISpec
   :members:
   :show-inheritance:
   :inherited-members:
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

Response Construction
---------------------

.. autoclass:: specargs.Response
   :exclude-members: __new__

Reusable OAS Components
-----------------------

.. autoclass:: specargs.oas.Response
   :members:

Exceptions
----------

.. autoexception:: specargs.decorators.DuplicateResponseCodeError
   :special-members:

.. autoexception:: specargs.decorators.UnregisteredResponseCodeError
   :special-members:

.. automodule:: specargs.in_poly
   :members:
   :exclude-members: InPoly, OneOf, AnyOf, AllOf
