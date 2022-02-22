from typing import Dict, Optional, Union, Type

from apispec import APISpec
from marshmallow import Schema
from webargs.core import ArgMap

from .in_poly import InPoly
from .oas import Response, ensure_response


class WebargsAPISpec(APISpec):
    '''TODO: Write docstring for WebargsAPISpec'''
    def __init__(self, title, version, openapi_version, plugins=(), **options):
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
        '''TODO: Write docstring for WebargsAPISpec.response'''
        response = ensure_response(response_or_argpoly, description=description, headers=headers)
        self.response_refs[response] = response_id
        self.components.response(response_id, response=response)
        return response

    def schema(self, schema_class_or_id: Union[Type[Schema], str]):
        '''TODO: Write docstring for WebargsAPISpec.schema'''
        # When used as a decorator with arguments
        if isinstance(schema_class_or_id, str):
            def decorator(schema_class: Type[Schema]):
                self.components.schema(schema_class_or_id, schema=schema_class)
                return schema_class

            return decorator

        # When passed a Schema class or used as a decorator without arguments
        schema_id = schema_class_or_id.__name__
        if schema_id.endswith("Schema"):
            # Remove 'Schema' from the end of the Schema class name unless the Schema class name is 'Schema'
            schema_id = schema_id[:-6] or schema_id

        self.components.schema(schema_id, schema=schema_class_or_id)
        return schema_class_or_id
