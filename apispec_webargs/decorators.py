from collections.abc import Iterable
import functools
from http import HTTPStatus
from typing import Optional, Union

from attrs import frozen

from .common import ArgMap, ensure_schema_or_inpoly
from .in_poly import InPoly
from .oas import Response, ensure_response

# TODO: Import parser depending on frawework in venv
from webargs.flaskparser import parser


@frozen
class Webargs:
    argpoly: Union[ArgMap, InPoly]
    location: str


def use_args(argpoly: Union[ArgMap, InPoly], *args, location: str = parser.DEFAULT_LOCATION, **kwargs):
    '''A wrapper around webargs' `use_args` decorator function

    This attaches attributes to the wrapped view function that are later used to populate the operation data for the
    generated API spec.
    
    Args:
        argpoly: A dictionary of marshmallow `Field` instances, a marshmallow `Schema` instance or class, or an object that inherits from
            :class:`~in_poly.InPoly`
        *args: Any other positional arguments accepted by webargs' `use_args`
        location: Identical to the `location` argument of webargs' `use_args`
        **kwargs: Any other keyword arguments accepted by webargs' `use_args`

    Raises:
        ValueError: If `argmap` is an :class:`~in_poly.InPoly` object and `location` is anything besides `"json"`
    '''
    if isinstance(argpoly, InPoly) and location != "json":
        raise ValueError("OneOf, AnyOf, and AllOf are only compatible with json body parameters!")

    schema_or_inpoly = ensure_schema_or_inpoly(argpoly)

    def decorator(func):
        func.webargs = getattr(func, "webargs", [])
        func.webargs.append(Webargs(schema_or_inpoly, location))
        inner_decorator = parser.use_args(schema_or_inpoly, *args, location = location, **kwargs)
        return inner_decorator(func)

    return decorator


def use_kwargs(*args, **kwargs):
    '''A decorator equivalent to :func:`use_args` with the keyword argument `as_kwargs` set to `True`'''
    return use_args(*args, as_kwargs=True, **kwargs)


class DuplicateResponseCodeError(Exception):
    '''An error to be raised when a status code is registered to a single view function/method more than once'''
    pass


def use_response(
    response_or_argpoly: Optional[Union[Response, Union[ArgMap, InPoly]]],
    *,
    status_code: HTTPStatus = HTTPStatus.OK,
    description: str = "",
    **headers: str
):
    '''A decorator function used for registering a response to a view function/method

    Args:
        response_or_argpoly: A :class:`~oas.Response` object, an :class:`~in_poly.InPoly` object, a marshmallow `Schema`
            class or instance, a dictionary of names to marshmallow `Field` objects, or `None`
        status_code: The status code under which the response is being registered. Defaults to `http.HTTPStatus.OK`
        description: The response description. Defaults to an empty string
        **headers: Any keyword arguments not listed above are taken as response header names and values

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
            # TODO: Allow response types other than Schema (i.e. Field)
            return (
                response.schema_or_inpoly.dump(data, many=isinstance(data, Iterable)) if response.schema_or_inpoly else "",
                status_code
            )

        return wrapper

    return decorator


def use_empty_response(**kwargs):
    '''Convenience decorator for registering an empty response to a view method
    
    Args:
        **kwargs: Any keyword arguments accepted by :func:`use_response`
    '''
    return use_response(None, **kwargs)

