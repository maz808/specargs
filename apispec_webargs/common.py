import enum
from typing import Callable, Union

from cattrs import GenConverter
from marshmallow import Schema
from marshmallow.schema import SchemaMeta
from webargs.core import ArgMap, Request

from webargs.flaskparser import parser


con = GenConverter()


def ensure_schema_or_factory(argmap: Union[ArgMap, SchemaMeta]) -> Union[Schema, Callable[[Request], Schema]]:
    '''TODO: Write docstring for ensure_schema_from_argmap()'''
    if isinstance(argmap, dict):
        return parser.schema_class.from_dict(argmap)()
    if isinstance(argmap, SchemaMeta):
        return argmap()
    if callable(argmap):
        return argmap
    TypeError(f"Unable to get Schema or Schema factory from {argmap}!")
