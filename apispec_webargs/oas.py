from typing import Dict, Optional, Tuple, Union

from attrs import define, field, converters, Factory
from cattrs.gen import make_dict_unstructure_fn, override
from marshmallow import Schema
from marshmallow.schema import SchemaMeta
from webargs.core import ArgMap

from .in_poly import InPoly
from .common import ensure_schema_or_factory, con


@define(eq=False)
class Response:
    '''TODO: Write docstring for Response'''
    schema: Optional[Union[Schema, InPoly]] = field(converter=converters.optional(ensure_schema_or_factory))
    description: str = ""
    headers: Dict[str, str] = Factory(dict)

    # Defined the __init__ method to add pre-converter typing to the `schema` argument
    def __init__(self, schema: Optional[Union[ArgMap, SchemaMeta]], *, description: str = "", headers: Tuple[Tuple[str, str]] = None):
        self.__attrs_init__(schema=schema, description=description, headers=headers or {})

    @property
    def content(self):
        '''TODO: Write docstring for Response.content'''
        return {"application/json": {"schema": self.schema}}


# Omit `schema` and default attributes and include `content` property if `schema` is trueish when converting to a dict
def _add_content_hook(response: Response) -> dict:
    out_dict = make_dict_unstructure_fn(
        Response,
        converter=con,
        headers=override(omit_if_default=True),
        schema=override(omit=True),
    )(response)
    if response.schema: out_dict["content"] = con.unstructure(response.content)
    return out_dict

con.register_unstructure_hook(Response, _add_content_hook)


def ensure_response(
    response_or_argmap: Union[Response, Union[ArgMap, SchemaMeta, InPoly]],
    *,
    description: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
):
    if isinstance(response_or_argmap, Response): return response_or_argmap
    if (
        callable(response_or_argmap) and
        not (isinstance(response_or_argmap, InPoly) or isinstance(response_or_argmap, SchemaMeta))
    ):
        raise TypeError("Schema factories are not currently supported!")

    schema_or_inpoly : Union[Schema, InPoly] = (
        ensure_schema_or_factory(response_or_argmap) if response_or_argmap else None
    )
    return Response(schema_or_inpoly, description=description, headers=headers)
