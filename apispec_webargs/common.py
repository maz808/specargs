from enum import Enum, auto
from typing import Dict, Union, TYPE_CHECKING, Type
import sys

from attrs import field, frozen
from cattrs import GenConverter
from marshmallow import Schema, fields

from webargs.flaskparser import parser

if TYPE_CHECKING:
    from in_poly import InPoly
else:
    InPoly = "InPoly"


class Framework(Enum):
    FLASK = auto()
    DJANGO = auto()
    TORNADO = auto()
    BOTTLE = auto()


class MissingFrameworkError(Exception):
    '''Raised when the project environment has not installed a supported framework'''
    pass


def _determine_framework():
    if "flask" in sys.modules:
        return Framework.FLASK
    if "django" in sys.modules:
        return Framework.DJANGO
    if "tornado" in sys.modules:
        return Framework.TORNADO
    if "bottle" in sys.modules:
        return Framework.BOTTLE
    raise MissingFrameworkError("A supported web framework (e.g. Flask, Django, etc.) must be installed!")


FRAMEWORK = _determine_framework()

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
