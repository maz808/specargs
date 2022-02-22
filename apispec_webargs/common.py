from inspect import signature
from typing import Dict, Union, TYPE_CHECKING, Type

from cattrs import GenConverter
from marshmallow import Schema, fields

from webargs.flaskparser import parser

if TYPE_CHECKING:
    from in_poly import InPoly
else:
    InPoly = "InPoly"


ArgMap = Union[Schema, Dict[str, Union[fields.Field, Type[fields.Field]]], Type[Schema]]

con = GenConverter()


def ensure_schema_or_inpoly(argpoly: Union[ArgMap, InPoly]) -> Union[Schema, InPoly]:
    '''Produces a marshmallow `Schema` or an :class:`InPoly` from the input if possible

    `Schema` and :class:`InPoly` instances are returned immediately. Dictionaries mapping names to marshmallow `Field`
    instances are converted into `Schema` instances using the webargs `parser`. `Schema` classes and factories with no
    arguments are called to produce `Schema` instances. All other objects raise a `TypeError`.

    Args:
        argmap_or_inpoly: The object from which to produce a `Schema` or :class:`InPoly` instance

    Raises:
        :exc:`TypeError`: If given an object from which a `Schema` or :class:`InPoly` instance cannot be produced
    '''
    from .in_poly import InPoly
    if isinstance(argpoly, Schema) or isinstance(argpoly, InPoly): return argpoly
    if isinstance(argpoly, dict): return parser.schema_class.from_dict(argpoly)()
    if callable(argpoly):
        # Assume argmap_or_inpoly is a Schema class or factory with no arguments
        try:
            possible_schema = argpoly()
        except TypeError:
            # TODO: Add logging for Schema factory with arguments error
            possible_schema = None
        if isinstance(possible_schema, Schema):
            return possible_schema
    raise TypeError(f"Unable to get Schema or InPoly from {argpoly}!")
