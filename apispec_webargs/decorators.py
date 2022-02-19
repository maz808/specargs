from collections import namedtuple
from collections.abc import Iterable
import functools
from http import HTTPStatus
from typing import Union

from marshmallow.schema import SchemaMeta
from webargs.core import ArgMap

from .in_poly import InPoly
from .oas import Response, ensure_response

# TODO: Import parser depending on frawework in venv
from webargs.flaskparser import parser


Webargs = namedtuple("Webargs", ("argmap", "location"))


def use_args(argmap: ArgMap, *args, location: str = parser.DEFAULT_LOCATION, **kwargs):
    '''TODO: Write docstring for use_args'''
    if callable(argmap) and not isinstance(argmap, InPoly):
        raise TypeError("Schema factories are not currently supported!")
    if isinstance(argmap, InPoly) and location != "json":
        raise ValueError("OneOf, AnyOf, and AllOf are only compatible with json body parameters!")

    def decorator(func):
        func.webargs = getattr(func, "webargs", [])
        func.webargs.append(Webargs(argmap, location))
        inner_decorator = parser.use_args(argmap, *args, location = location, **kwargs)
        return inner_decorator(func)

    return decorator


def use_kwargs(*args, **kwargs):
    '''TODO: Write docstring for use_kwargs'''
    return use_args(*args, as_kwargs=True, **kwargs)


class DuplicateResponseCodeError(Exception):
    '''TODO: Write docstring for DuplicateResponseCodeError'''
    pass


def use_response(
    response_or_argmap: Union[Response, Union[ArgMap, SchemaMeta, InPoly]],
    *,
    status_code: HTTPStatus = HTTPStatus.OK,
    description: str = "",
    **headers: str
):
    '''TODO: Write docstring for use_response'''
    response = ensure_response(response_or_argmap, description=description, headers=headers)

    def decorator(func):
        func.responses = getattr(func, "responses", {})
        if status_code in func.responses:
            raise DuplicateResponseCodeError(f"\nStatus code '{status_code}' is already registered to '{func.__qualname__}'!")

        func.responses[status_code] = response

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = func(*args, **kwargs)
            # TODO: Allow response types other than Schema (i.e. marshmallow.fields)
            return (
                response.schema.dump(data, many=isinstance(data, Iterable)) if response.schema else "",
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