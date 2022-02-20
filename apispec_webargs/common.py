from typing import Union, TYPE_CHECKING

from cattrs import GenConverter
from marshmallow import Schema
from marshmallow.schema import SchemaMeta

from webargs.flaskparser import parser

if TYPE_CHECKING:
    from in_poly import InPoly
else:
    InPoly = "InPoly"


con = GenConverter()


def ensure_schema_or_inpoly(obj) -> Union[Schema, InPoly]:
    '''Produces a marshmallow `Schema` or an :class:`InPoly` from the input if possible

    `Schema` and :class:`InPoly` instances are returned immediately. `Schema` classes are called to produce
    `Schema` instances. Dictionaries mapping names to marshmallow `Field` instances are converted into `Schema`
    instances using the webargs `parser`. All other objects raise a `TypeError`.

    Args:
        obj: The object from which to produce a `Schema` or :class:`InPoly` instance

    Raises:
        :exc:`TypeError`: If given an object from which a `Schema` or :class:`InPoly` instance cannot be produced
    '''
    from .in_poly import InPoly
    if isinstance(obj, Schema) or isinstance(obj, InPoly): return obj
    if isinstance(obj, SchemaMeta): return obj()
    if isinstance(obj, dict): return parser.schema_class.from_dict(obj)()
    raise TypeError(f"Unable to get Schema or InPoly from {obj}!")

