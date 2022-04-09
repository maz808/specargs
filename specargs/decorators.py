import functools
from http import HTTPStatus
from typing import Any, Callable, Optional, Union, Tuple

from marshmallow import Schema
from webargs import fields

from .common import ArgMap, Webargs
from .view_response import ViewResponse
from .framework import parser, make_response
from .in_poly import InPoly
from .oas import ensure_response, Response


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


class UnregisteredResponseCodeError(Exception):
    '''An exception that's raised when a view function/method returns an unregistered status code

    The status code of a :class:`~specargs.Response` returned by a view function/method must be registered to the view
    function/method using :func:`~specargs.use_response` or :func:`~specargs.use_empty_response`.
    '''
    pass


def _get_response_data_and_status(data: Any, default_status: HTTPStatus) -> Tuple[Any, HTTPStatus]:
    if isinstance(data, ViewResponse):
        return data.data, data.status_code
    return data, default_status


def _dump_response_schema(obj: Any, schema: Optional[Union[Schema, InPoly, fields.Field]]):
    is_list_tuple_or_set = any(isinstance(obj, type_) for type_ in (list, tuple, set))
    if isinstance(schema, Schema) or isinstance(schema, InPoly): return schema.dump(obj, many=is_list_tuple_or_set)
    if isinstance(schema, fields.Field): return schema.serialize("unused", obj, lambda o, *_: o)
    if schema is None: return ""


def use_response(
    response_or_argpoly: Optional[Union[Response, Union[fields.Field, ArgMap, InPoly]]],
    *,
    status_code: Union[HTTPStatus, int] = HTTPStatus.OK,
    description: str = "",
    **headers: str
) -> Callable[..., Callable]:
    '''A decorator function used for registering a response to a view function/method

    Args:
        response_or_argpoly: A :class:`~oas.Response` object, an :class:`~in_poly.InPoly` object, a
            :class:`marshmallow.Schema` class or instance, a dictionary of names to :mod:`marshmallow.fields`, or
            `None`. Determines the content of the corresponding `response` clause in the generated OpenAPI spec and
            whether/how the data returned by the decorated view function/method is serialized
        status_code: The status code under which the response is being listed in the generated OpenAPI spec. Also used
            as the status code for the decorated view function/method response. Defaults to `http.HTTPStatus.OK`
        description: The response description. Defaults to an empty string. Ignored if `response_or_argpoly` is an
            :class:`oas.Response` object
        **headers: Any keyword arguments not listed above are taken as response header names and values. Ignored if
            `response_or_argpoly` is an :class:`oas.Response` object

    Raises:
        :exc:`DuplicateResponseCodeError`: If a status code is registered to the same view function/method more than
            once
        :exc:`UnregisteredResponseCodeError`: If the status code of a :class:`~specargs.Response` returned by a view
            function/method has not be registered to the view function/method
    '''
    if isinstance(status_code, int): status_code = HTTPStatus(status_code)
    response = ensure_response(response_or_argpoly, description=description, headers=headers)

    def decorator(func):
        func.responses = getattr(func, "responses", {})
        if status_code in func.responses:
            raise DuplicateResponseCodeError(
                f"\nStatus code '{status_code}' is already registered to '{func.__qualname__}'!"
            )

        func.responses[status_code] = response

        is_resp_wrapper = "is_resp_wrapper"
        if getattr(func, is_resp_wrapper, False): func = func.__wrapped__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            view_data = func(*args, **kwargs)
            response_data, response_status = _get_response_data_and_status(view_data, status_code)

            try:
                schema = func.responses[response_status].schema
            except KeyError:
                raise UnregisteredResponseCodeError(
                    f"Status code '{response_status}' has not been registered to '{func.__qualname__}'!"
                )

            return make_response(_dump_response_schema(response_data, schema), response_status)

        setattr(wrapper, is_resp_wrapper, True)
        return wrapper

    return decorator


def use_empty_response(**kwargs) -> Callable[..., Callable]:
    '''Convenience decorator for registering an empty response to a view method
    
    Args:
        **kwargs: Any keyword arguments accepted by :func:`use_response`
    '''
    return use_response(None, **kwargs)
