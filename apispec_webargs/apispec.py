from typing import Dict, Optional, Union

from apispec import APISpec
from marshmallow.schema import SchemaMeta
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
        response_or_argmap: Union[Response, Union[ArgMap, SchemaMeta, InPoly]],
        *,
        description: str = "",
        **headers: str
    ) -> Response:
        '''TODO: Write docstring for WebargsAPISpec.response'''
        response = ensure_response(response_or_argmap, description=description, headers=headers)
        self.response_refs[response] = response_id
        self.components.response(response_id, response=response)
        return response

    def schema(self, schema_class_or_id: Union[SchemaMeta, str]):
        '''TODO: Write docstring for WebargsAPISpec.schema'''
        # When passed a Schema class or used as a decorator without arguments
        if isinstance(schema_class_or_id, SchemaMeta):
            schema_id = schema_class_or_id.__name__
            if schema_id.endswith("Schema"):
                # Remove 'Schema' from the end of the Schema class name unless the Schema class name is 'Schema'
                schema_id = schema_id[:-6] or schema_id

            self.components.schema(schema_id, schema=schema_class_or_id)
            return schema_class_or_id

        # When used as a decorator with arguments
        def decorator(schema_class: SchemaMeta):
            self.components.schema(schema_class_or_id, schema=schema_class)
            return schema_class

        return decorator
