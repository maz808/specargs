from enum import Enum, auto
import os
from typing import Dict, Union, TYPE_CHECKING, Type
import sys

from attrs import field, frozen
from cattrs import GenConverter
from marshmallow import Schema, fields
import webargs.core

if TYPE_CHECKING:
    from in_poly import InPoly
else:
    InPoly = "InPoly"


class Framework(Enum):
    FLASK = "flask"
    DJANGO = "django"
    TORNADO = "tornado"
    BOTTLE = "bottle"


class MissingFrameworkError(Exception):
    '''Raised when the project environment has not installed a supported framework'''
    pass


class MultipleFrameworkError(Exception):
    '''Raised when the project environment has installed multiple supported frameworks'''
    pass


def _determine_framework():
    active_framework = None
    for framework in Framework:
        if framework.value in sys.modules:
            if active_framework:
                raise MultipleFrameworkError("Multiple frameworks in the environment is not supported!")
            active_framework = framework

    if not active_framework:
        raise MissingFrameworkError("A supported web framework (e.g. Flask, Django, etc.) must be installed!")

    return active_framework


FRAMEWORK = _determine_framework() if not os.environ.get("ASWA_DOCS", False) else None

if not FRAMEWORK: parser = webargs.core.Parser()
elif FRAMEWORK == Framework.FLASK: from webargs.flaskparser import parser
elif FRAMEWORK == Framework.DJANGO: from webargs.djangoparser import parser
elif FRAMEWORK == Framework.TORNADO: from webargs.tornadoparser import parser
elif FRAMEWORK == Framework.BOTTLE: from webargs.bottleparser import parser

ArgMap = Union[Schema, Dict[str, Union[fields.Field, Type[fields.Field]]], Type[Schema]]

con = GenConverter()


@frozen
class Webargs:
    schema_or_inpoly: Union[Schema, InPoly] = field(converter=lambda x: ensure_schema_or_inpoly(x))
    location: str


def ensure_schema_or_inpoly(argpoly: Union[ArgMap, InPoly]) -> Union[Schema, InPoly]:
    '''Produces a marshmallow `Schema` or an :class:`InPoly` from the input if possible

    `Schema` and :class:`InPoly` instances are returned immediately. Dictionaries mapping names to marshmallow `Field`
    instances are converted into `Schema` instances using the webargs `parser`. `Schema` classes are called to produce
    `Schema` instances. All other objects raise a `TypeError`.

    Args:
        argpoly: The object from which to produce a `Schema` or :class:`InPoly` instance

    Raises:
        :exc:`TypeError`: If given an object from which a `Schema` or :class:`InPoly` instance cannot be produced
    '''
    from .in_poly import InPoly
    if isinstance(argpoly, Schema) or isinstance(argpoly, InPoly): return argpoly
    if isinstance(argpoly, dict): return parser.schema_class.from_dict(argpoly)()
    if isinstance(argpoly, type(Schema)): return argpoly()
    raise TypeError(f"Unable to produce Schema or InPoly from {argpoly}!")
