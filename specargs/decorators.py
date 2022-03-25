import functools
from http import HTTPStatus
from typing import Any, Callable, Optional, Union

from marshmallow import Schema
from webargs import fields

from .common import ArgMap, Webargs, parser
from .in_poly import InPoly
from .oas import Response, ensure_response


def use_args(argpoly: Union[ArgMap, InPoly], *args, location: str = parser.DEFAULT_LOCATION, **kwargs) -> Callable[..., Callable]:
    '''A wrapper around webargs' :meth:`~webargs.core.Parser.use_args` decorator function

    This attaches attributes to the wrapped view function that are later used to populate the operation data for the
    generated API spec.
    
    Args:
        argpoly: A dictionary of :mod:`webargs.fields`, a :class:`marshmallow.Schema` instance or class, or an object that inherits from
            :class:`~in_poly.InPoly` to be used for request argument parsing
        *args: Any other positional arguments accepted by webargs' :meth:`~webargs.core.Parser.use_args`
        location: Identical to the `location` argument of webargs' :meth:`~webargs.core.Parser.use_args`
        **kwargs: Any other keyword arguments accepted by webargs' :meth:`~webargs.core.Parser.use_args`

    Raises:
        ValueError: If `argmap` is an :class:`~in_poly.InPoly` object and `location` is anything besides `"json"`
    '''
    if isinstance(argpoly, InPoly) and location != "json":
        raise ValueError("OneOf, AnyOf, and AllOf are only compatible with json body parameters!")

    def decorator(func):
        func.webargs = getattr(func, "webargs", [])
        func.webargs.append(Webargs(argpoly, location))
        inner_decorator = parser.use_args(argpoly, *args, location = location, **kwargs)
        return inner_decorator(func)

    return decorator


def use_kwargs(*args, **kwargs) -> Callable[..., Callable]:
    '''A decorator equivalent to :func:`use_args` with the keyword argument `as_kwargs` set to `True`'''
    return use_args(*args, as_kwargs=True, **kwargs)


class DuplicateResponseCodeError(Exception):
    '''An exception that's raised when a status code is registered to a single view function/method more than once'''
    pass


def _dump_response(obj: Any, response: Response):
    schema = response.schema
    is_list_tuple_or_set = any(isinstance(obj, type_) for type_ in (list, tuple, set))
    if isinstance(schema, Schema) or isinstance(schema, InPoly): return schema.dump(obj, many=is_list_tuple_or_set)
    if isinstance(schema, fields.Field): return schema.serialize("unused", obj, lambda o, *_: o)
    if schema is None: return ""


def use_response(
    response_or_argpoly: Optional[Union[Response, Union[ArgMap, InPoly]]],
    *,
    status_code: HTTPStatus = HTTPStatus.OK,
    description: str = "",
    **headers: str
) -> Callable[..., Callable]:
    '''A decorator function used for registering a response to a view function/method

    Args:
        response_or_argpoly: A :class:`~oas.Response` object, an :class:`~in_poly.InPoly` object, a marshmallow `Schema`
            class or instance, a dictionary of names to marshmallow `Field` objects, or `None`. Determines the content
            of the corresponding `response` clause in the generated OpenAPI spec and whether/how the data returned by
            the decorated view function/method is serialized
        status_code: The status code under which the response is being listed in the generated OpenAPI spec. Also used
            as the status code for the decorated view function/method response. Defaults to `http.HTTPStatus.OK`
        description: The response description. Defaults to an empty string. Ignored if `response_or_argpoly` is a
            :class:`~Response` object
        **headers: Any keyword arguments not listed above are taken as response header names and values. Ignored if
            `response_or_argpoly` is a :class:`~Response` object

    Raises:
        :exc:`DuplicateResponseCodeError`: If a status code is registered to the same view function/method more than
            once
    '''
    response = ensure_response(response_or_argpoly, description=description, headers=headers)

    def decorator(func):
        func.responses = getattr(func, "responses", {})
        if status_code in func.responses:
            raise DuplicateResponseCodeError(f"\nStatus code '{status_code}' is already registered to '{func.__qualname__}'!")

        func.responses[status_code] = response

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = func(*args, **kwargs)
            # TODO: Determine return value based on framework (e.g. Flask's make_response vs Django's HttpResponse)
            return (_dump_response(data, response), status_code)

        return wrapper

    return decorator


def use_empty_response(**kwargs) -> Callable[..., Callable]:
    '''Convenience decorator for registering an empty response to a view method
    
    Args:
        **kwargs: Any keyword arguments accepted by :func:`use_response`
    '''
    return use_response(None, **kwargs)
