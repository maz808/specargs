__version__ = '0.1.0'

from collections.abc import Iterable
import functools
from http import HTTPStatus
from typing import Optional, Tuple, Union

from marshmallow import Schema
from marshmallow.schema import SchemaMeta
from webargs import validate, fields
from webargs.core import ArgMap

from .common import ensure_schema_or_factory
from .in_poly import InPoly


def use_args(argmap: ArgMap, *args, **kwargs):
    '''TODO: Write docstring for use_args'''
    from webargs.flaskparser import use_args, parser
    location = kwargs.get("location") or parser.DEFAULT_LOCATION
    if callable(argmap) and not isinstance(argmap, InPoly):
        raise TypeError("Schema factories are not currently supported!")
    if isinstance(argmap, InPoly) and location != "json":
        raise ValueError("OneOf, AnyOf, and AllOf are only compatible with json body parameters!")

    def decorator(func):
        func.webargs = getattr(func, "webargs", [])
        func.webargs.append(((argmap, *args), {**kwargs, "location": location}))
        inner_decorator = use_args(argmap, *args, **kwargs)
        return inner_decorator(func)

    return decorator


def use_kwargs(*args, **kwargs):
    '''TODO: Write docstring for use_kwargs'''
    kwargs["as_kwargs"] = True
    return use_args(*args, **kwargs)


class MultipleOf(validate.Validator):
    """Validator which succeeds if the ``value`` passed to it is
    a multiple of ``multiply``.

    :param multiply: The object to compare to.
    :param error: Error message to raise in case of a validation error.
        Can be interpolated with `{multiply}`.
    """

    default_message = "Must be a multiple of {multiply}."

    def __init__(self, multiply, *, error: Optional[str] = None):
        if multiply <= 0: raise ValueError("'multiply' argument of MultipleOf constructor must be a positive number!")
        self.multiply = multiply
        self.error = error or self.default_message  # type: str

    def _repr_args(self) -> str:
        return f"multiply={self.multiply!r}"

    def _format_error(self, value: validate._T) -> str:
        return self.error.format(input=value, multiply=self.multiply)

    def __call__(self, value: validate._T) -> validate._T:
        if self.multiply % value != 0:
            raise validate.ValidationError(self._format_error(value))
        return value


class ResponseConflictError(Exception):
    '''TODO: Write docstring for ResponseConflictError'''
    pass


def response(
    argmap: Union[ArgMap, SchemaMeta, InPoly],
    *,
    description: str = "",
    headers: Tuple[Tuple[str,str]] = None,
    status_code: HTTPStatus = HTTPStatus.OK,
):
    '''TODO: Write docstring for response'''
    headers = headers or tuple()
    schema_or_inpoly : Union[Schema, InPoly] = ensure_schema_or_factory(argmap) if argmap else None

    def decorator(func):
        func.responses = getattr(func, "responses", {})
        if status_code in func.responses:
            raise ResponseConflictError(f"\nStatus code '{status_code}' registered to '{func.__qualname__}' multiple times!")
        func.responses[status_code] = (schema_or_inpoly, description, headers)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data = func(*args, **kwargs)
            if not schema_or_inpoly: return "", status_code
            return schema_or_inpoly.dump(data, many=isinstance(data, Iterable)), status_code

        return wrapper

    return decorator
