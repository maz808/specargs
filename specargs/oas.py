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
    '''Stores metadata representing a reusable OpenAPI specification response object

    This class should only be instantiated using the :meth:`~specargs.WebargsAPISpec.response` method of the
    :class:`~specargs.WebargsAPISpec` class.

    The :attr:`schema` attribute of this class is also used for data serialization when provided to
    :func:`specargs.use_response`.
    '''
    #: A :class:`marshmallow.Schema`, an :class:`~specargs.in_poly.InPoly` object, or a :class:`marshmallow.fields.Field`. Determines the :attr:`~Response.content` of the generated OpenAPI response object. Also determines serialization of response data when provided to :func:`specargs.use_response`
    schema: Optional[Union[Schema, InPoly, fields.Field]] = field(
        converter=converters.optional(lambda obj: ensure_field_schema_or_inpoly(obj)))
    #: The response description
    description: str = ""
    #: A dictionary of the :class:`Response` header names to values
    headers: Dict[str, str] = Factory(dict)

    def __init__(
        self,
        argpoly_or_field: Optional[Union[ArgMap, InPoly, fields.Field]],
        *,
        description: str = "",
        headers: Dict[str, str] = None
    ):
        '''Initializes a :class:`Response` object
        
        Args:
            argpoly_or_field: An :class:`~specargs.in_poly.InPoly` object, a :class:`marshmallow.Schema` class or instance, a
                dictionary of names to :mod:`marshmallow.fields`, or `None`. Determines the content of the corresponding
                `response` clause in the generated OpenAPI spec and whether/how the data returned by the decorated view
                function/method is serialized
            description: The response object description
            headers: A dictionary of response header names to values
        '''
        self.__attrs_init__(schema=argpoly_or_field, description=description, headers=headers or {})

    @property
    def content(self) -> dict:
        '''A dictionary that represents the `content` section of the generated OpenAPI response object'''
        content_type = (
            "application/json" if isinstance(self.schema, Schema) or isinstance(self.schema, InPoly) else
            "text/html"
        )
        return {content_type: {"schema": self.schema}}


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
