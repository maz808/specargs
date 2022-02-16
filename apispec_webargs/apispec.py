from typing import Dict, Union

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
