from abc import ABC, abstractmethod
import os
from typing import Any, Dict, Optional, Type, Union

from apispec import APISpec
from marshmallow import Schema
from webargs.core import ArgMap

from .in_poly import InPoly
from .oas import Response, ensure_response


class WebargsAPISpec(APISpec):
    '''Stores metadata that describes a RESTful API and generates an OpenAPI spec from that metadata

    This class adds functionality to :class:`apispec.APISpec` that allows for definition of reusable OpenAPI response
    and schema objects. This class also adds convenient extraction of operation metadata from components of the
    supported frameworks (e.g. Flask, Tornado, etc.).
    '''
    def __init__(self, title, version, openapi_version, plugins=(), **options):
        '''Initializes a :class:`WebargsAPISpec` object
        
        This accepts the same arguments as the constructor for :class:`apispec.APISpec`
        '''
        super().__init__(title, version, openapi_version, plugins, **options)
        self.response_refs: Dict[Response, str] = {}

    def response(
        self,
        response_id: str,
        response_or_argpoly: Union[Response, Union[ArgMap, InPoly]],
        *,
        description: str = "",
        **headers: str
    ) -> Response:
        '''Registers a resuable OAS response object and returns it as an :class:`oas.Response` easy reuse

        Args:
            response_id: The name of the response as it will appear in the OpenAPI spec
            response_or_argpoly: A :class:`oas.Response` object, an :class:`~in_poly.InPoly` object, a marshmallow
                `Schema` class or instance, a dictionary of names to marshmallow `Field` objects, or `None`. Determines
                the content of the generated OpenAPI response object
            description: The description of the generated OpenAPI response object. Ignored if `response_or_argpoly` is
                a :class:`~oas.Response` object
            **headers: Any keyword arguments not listed above are taken as response header names and values. Ignored if
                if `response_or_argpoly` is a :class:`oas.Response` object

        Returns:
            The value of `response_or_argpoly` if a :class:`~oas.Response` object was provided. Otherwise, a new
            :class:`~oas.Response` instance created from `response_or_argpoly`, `description`, and `**headers`
        '''
        response = ensure_response(response_or_argpoly, description=description, headers=headers)
        self.response_refs[response] = response_id
        self.components.response(response_id, response=response)
        return response

    def schema(self, schema_class_or_name: Union[Type[Schema], str], custom_name: Optional[str] = None):
        '''Registers a :class:`marshmallow.Schema` as an OpenAPI spec schema

        This method can be used one of three ways:

        #. As a :class:`marshmallow.Schema` class decorator with no arguments::

            spec = WebargsAPISpec(...)

            # This will result in an OAS schema with the name "Example"
            @spec.schema
            class ExampleSchema(marshmallow.Schema):
                ...

        #. As a :class:`marshmallow.Schema` class decorator with arguments::

            spec = WebargsAPISpec(...)

            # This will result in an OAS schema with the name "CustomName"
            @spec.schema("CustomName")
            class ExampleSchema(marshmallow.Schema):
                ...

        #. As a method that accepts a :class:`marshmallow.Schema` class and optionally a string name::

            spec = WebargsAPISpec(...)

            class ExampleSchema(marshmallow.Schema):
                ...

            # This will result in an OAS schema with the name "Example"
            spec.schema(ExampleSchema)
            # This will result in an OAS schema with the name "CustomName"
            spec.schema(ExampleSchema, "CustomName")

        Args:
            schema_class_or_name: A :class:`marshmallow.Schema` class or, if used as decorator, a string containing the
                name of the OpenAPI schema that will be generated
            custom_name: The name of the generated OpenAPI schema when this method is not used as a decorator
        '''
        # When used as a decorator with arguments
        if isinstance(schema_class_or_name, str):
            def decorator(schema_class: Type[Schema]):
                self.components.schema(schema_class_or_name, schema=schema_class)
                return schema_class

            return decorator

        # When passed a Schema class or used as a decorator without arguments
        if custom_name: schema_name = custom_name
        else:
            schema_name = schema_class_or_name.__name__
            # Remove 'Schema' from the end of the Schema class name unless the Schema class name is 'Schema'
            if schema_name.endswith("Schema"): schema_name = schema_name[:-6] or schema_name

        self.components.schema(schema_name, schema=schema_class_or_name)
        return schema_class_or_name

    @abstractmethod
    def create_paths(self, framework_obj: Any):
        '''Creates the `paths` section of the OpenAPI spec from the appropriate framework object

        Args:
            framework_obj: The object corresponding to the framework being used.

        The list of supported frameworks and accepted objects is as follows:

        - Flask: :class:`flask.Flask`'''
        from .framework import create_paths
        create_paths(self, framework_obj)
