from typing import Dict, Optional, Tuple, Union

from attrs import frozen, field, converters, Factory
from cattrs.gen import make_dict_unstructure_fn, override
from marshmallow import Schema

from .in_poly import InPoly
from .common import ensure_schema_or_inpoly, con, ArgMap


@frozen(eq=False)
class Response:
    '''TODO: Write docstring for Response'''
    schema_or_inpoly: Optional[Union[Schema, InPoly]] = field(converter=converters.optional(ensure_schema_or_inpoly))
    description: str = ""
    headers: Dict[str, str] = Factory(dict)

    def __init__(
        self,
        argpoly: Optional[Union[ArgMap, InPoly]],
        *,
        description: str = "",
        headers: Tuple[Tuple[str, str]] = None
    ):
        self.__attrs_init__(schema_or_inpoly=argpoly, description=description, headers=headers or {})

    @property
    def content(self):
        '''TODO: Write docstring for Response.content'''
        return {"application/json": {"schema": self.schema_or_inpoly}}


# Omit `schema` and default attributes and include `content` property if `schema` is trueish when converting to a dict
def _add_content_hook(response: Response) -> dict:
    out_dict = make_dict_unstructure_fn(
        Response,
        converter=con,
        headers=override(omit_if_default=True),
        schema_or_inpoly=override(omit=True),
    )(response)
    if response.schema_or_inpoly: out_dict["content"] = con.unstructure(response.content)
    return out_dict

con.register_unstructure_hook(Response, _add_content_hook)


def ensure_response(
    response_or_argpoly: Union[Response, Union[ArgMap, InPoly]],
    *,
    description: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
):
    if isinstance(response_or_argpoly, Response): return response_or_argpoly
    return Response(response_or_argpoly, description=description, headers=headers)
