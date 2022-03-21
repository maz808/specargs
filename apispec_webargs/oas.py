from collections.abc import Iterable
from typing import Any, Dict, Optional, Tuple, Union

from attrs import frozen, field, converters, Factory
from cattrs.gen import make_dict_unstructure_fn, override
from marshmallow import Schema
from webargs import fields

from .in_poly import InPoly
from .common import ensure_schema_or_inpoly, con, ArgMap


def ensure_field_schema_or_inpoly(
    field_or_argpoly: Union[fields.Field, ArgMap, InPoly]
) -> Union[fields.Field, Schema, InPoly]:
    if isinstance(field_or_argpoly, fields.Field): return field_or_argpoly
    if isinstance(field_or_argpoly, type(fields.Field)):
        possible_field = field_or_argpoly()
        if isinstance(possible_field, fields.Field): return possible_field
    try:
        return ensure_schema_or_inpoly(field_or_argpoly)
    except TypeError:
        raise TypeError(f"Unable to produce Field, Schema, or Inpoly from {field_or_argpoly}!")


@frozen(eq=False)
class Response:
    '''TODO: Write docstring for Response'''
    schema: Optional[Union[Schema, InPoly, fields.Field]] = field(
        converter=converters.optional(lambda obj: ensure_field_schema_or_inpoly(obj)))
    description: str = ""
    headers: Dict[str, str] = Factory(dict)

    def __init__(
        self,
        argpoly_or_field: Optional[Union[ArgMap, InPoly]],
        *,
        description: str = "",
        headers: Tuple[Tuple[str, str]] = None
    ):
        self.__attrs_init__(schema=argpoly_or_field, description=description, headers=headers or {})

    @property
    def content(self):
        '''TODO: Write docstring for Response.content'''
        content_type = (
            "application/json" if isinstance(self.schema, Schema) or isinstance(self.schema, InPoly) else
            "text/html"
        )
        return {content_type: {"schema": self.schema}}

    def dump(self, obj: Any) -> dict:
        schema = self.schema
        is_list_tuple_or_set = any(isinstance(obj, type_) for type_ in (list, tuple, set))
        if isinstance(schema, Schema) or isinstance(schema, InPoly): return schema.dump(obj, many=is_list_tuple_or_set)
        if isinstance(schema, fields.Field): return schema.serialize("unused", obj, lambda o, *_: o)
        if schema is None: return ""


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
    response_or_argpoly: Union[Response, Union[ArgMap, InPoly]],
    *,
    description: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
):
    if isinstance(response_or_argpoly, Response): return response_or_argpoly
    return Response(response_or_argpoly, description=description, headers=headers)
