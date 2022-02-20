from abc import ABC, abstractclassmethod, abstractmethod
from functools import reduce
from operator import iand
from typing import Any, ClassVar, Tuple, Union

from attrs import define, field
from marshmallow import Schema, EXCLUDE, ValidationError
from marshmallow.schema import SchemaMeta
from webargs.core import ArgMap

# TODO: Make Request type dependent on framework being used
# import sys
# if <framework-package> in sys.modules
from flask import Request

from .common import ensure_schema_or_inpoly, con


def argmaps_to_schemas(argmap_or_argmaps: Tuple[Union[ArgMap, SchemaMeta]]) -> Tuple[Schema]:
    '''TODO: Write docstring for argmaps_to_schemas'''
    if isinstance(argmap_or_argmaps, tuple):
        return tuple(ensure_schema_or_inpoly(argmap) for argmap in argmap_or_argmaps)
    return ensure_schema_or_inpoly(argmap_or_argmaps)


@define
class InPoly(ABC):
    '''TODO: Write docstring for InPoly'''
    schemas: Tuple[Schema] = field(converter=argmaps_to_schemas)

    def __init__(self, *schemas: Union[ArgMap, SchemaMeta]):
        '''TODO: Write docstring for InPoly.__init__'''
        self.__attrs_init__(schemas)

    def __attrs_post_init__(self):
        pass

    def _determine_shared_keys(self):
        keys_to_schemas = {}
        for schema in self.schemas:
            for key in schema.fields.keys():
                keys_to_schemas[key] = (*keys_to_schemas.get(key, ()), schema)

        self.shared_keys_to_schemas = {key: schemas for key, schemas in keys_to_schemas.items() if len(schemas) > 1}

    @property
    @abstractclassmethod
    def string_rep(cls) -> str:
        ...

    @abstractmethod
    def dump(self, obj: Any, *, many: bool = False) -> dict:
        ...

    @abstractmethod
    def __call__(self, request: Request) -> Schema:
        ...


con.register_unstructure_hook(InPoly, lambda ip: {ip.string_rep: ip.schemas})


# TODO: Improve initialization of OneOfConflictError (args to generate message)
class OneOfConflictError(Exception):
    '''TODO: Write docstring for OneOfConflictError'''
    pass


# TODO: Improve initialization of OneOfValidationError (args to generate message)
class OneOfValidationError(Exception):
    '''TODO: Write docstring for OneOfValidationError'''
    pass


class OneOf(InPoly):
    '''TODO: Write docstring for OneOf'''
    string_rep: ClassVar[str] = "oneOf"

    def __init__(self, *schemas: Schema, unknown: str = EXCLUDE):
        '''TODO: Write docstring for OneOf.__init__'''
        super().__init__(*schemas)
        for schema in self.schemas:
            schema.unknown = unknown

    def __call__(self, request: Request) -> Schema:
        valid_schemas = tuple(schema for schema in self.schemas if len(schema.validate(request.json)) == 0)
        if len(valid_schemas) > 1:
            raise OneOfConflictError(
                f"Request data is valid for multiple Schemas in "
                f"OneOf({', '.join(type(schema).__name__ for schema in self.schemas)})!"
            )

        if len(valid_schemas) == 0:
            raise OneOfValidationError(
                f"Request data is invalid for all Schemas in "
                f"OneOf({', '.join(type(schema).__name__ for schema in self.schemas)})!"
            )

        return valid_schemas[0]

    def dump(self, obj: Any, *, many: bool = False) -> dict:
        '''TODO: Add docstring for OneOf.dump()'''
        valid_dumps = []
        for schema in self.schemas:
            try: dump = schema.dump(obj)
            except ValueError: continue
            if len(schema.validate(dump)) > 0: continue
            valid_dumps.append(dump)

        if len(valid_dumps) > 1:
            raise OneOfConflictError(
                f"'{type(obj).__name__}' is valid for multiple Schemas in "
                f"OneOf({', '.join(type(schema).__name__ for schema in self.schemas)})!"
            )

        if len(valid_dumps) == 0:
            raise OneOfValidationError(
                f"'{type(obj).__name__}' is invalid for all Schemas in "
                f"OneOf({', '.join(type(schema).__name__ for schema in self.schemas)})!"
            )

        return valid_dumps[0]


# TODO: Improve initialization of AnyOfValidationError (args to generate message)
class AnyOfValidationError(Exception):
    '''TODO: Write docstring for AnyOfValidationError'''
    pass


# TODO: Improve initialization of AnyOfConflictError (args to generate message)
class AnyOfConflictError(Exception):
    '''TODO: Write docstring for AnyOfConflictError'''
    pass


class AnyOf(InPoly):
    '''TODO: Write docstring for AnyOf'''
    string_rep: ClassVar[str] = "anyOf"

    def __attrs_post_init__(self):
        self._determine_shared_keys()

    def __call__(self, request: Request) -> Schema:
        valid_schema_loads = {}
        for schema in self.schemas:
            try: load = schema.load(request.json, unknown=EXCLUDE)
            except ValidationError: continue
            valid_schema_loads[schema] = load

        if len(valid_schema_loads) == 0:
            raise AnyOfValidationError(
                f"Request data is invalid for all Schemas in "
                f"AnyOf({', '.join(type(schema).__name__ for schema in self.schemas)})!"
            )

        conflicting_keys = any(
            valid_schema_loads[schema][shared_key] != valid_schema_loads[schemas[0]][shared_key]
            for shared_key, schemas in self.shared_keys_to_schemas.items()
            for schema in schemas if schema in valid_schema_loads
        )
        if conflicting_keys:
            raise AnyOfConflictError(
                f"Schemas in AnyOf({', '.join(type(schema).__name__ for schema in self.schemas)}) have conflicting keys!"
            )

        return Schema.from_dict({name: field for schema in valid_schema_loads for name, field in schema.fields.items()})()

    def dump(self, obj: Any, *, many: bool = False) -> dict:
        '''TODO: Add docstring for AnyOf.dump()'''
        valid_schema_dumps = {}
        for schema in self.schemas:
            try: dump = schema.dump(obj)
            except ValueError: continue
            if len(schema.validate(dump)) > 0: continue
            valid_schema_dumps[schema] = dump

        if len(valid_schema_dumps) == 0:
            raise AnyOfValidationError(
                f"'{type(obj).__name__}' is invalid for all Schemas in "
                f"AnyOf({', '.join(type(schema).__name__ for schema in self.schemas)})!"
            )

        conflicting_keys = any(
            valid_schema_dumps[schema][shared_key] != valid_schema_dumps[schemas[0]][shared_key]
            for shared_key, schemas in self.shared_keys_to_schemas.items()
            for schema in schemas if schema in valid_schema_dumps
        )
        if conflicting_keys:
            raise AnyOfConflictError(
                f"Schemas in AnyOf({', '.join(type(schema).__name__ for schema in self.schemas)}) have conflicting keys!"
            )

        return {k:v for dump in valid_schema_dumps.values() for k,v in dump.items()}


# TODO: Improve initialization of AllOfConflictError (args to generate message)
class AllOfConflictError(Exception):
    '''TODO: Write docstring for AllOfConflictError'''
    pass


# TODO: Improve initialization of AllOfValidationError (args to generate message)
class AllOfValidationError(Exception):
    '''TODO: Write docstring for AllOfValidationError'''
    pass


class AllOf(InPoly):
    '''TODO: Write docstring for AllOf'''
    string_rep: ClassVar[str] = "allOf"

    def __attrs_post_init__(self):
        self._determine_shared_keys()

    def __call__(self, request: Request) -> Schema:
        try:
            schema_loads = {schema: schema.load(request.json, unknown=EXCLUDE) for schema in self.schemas}
        except ValidationError as e:
            raise AllOfValidationError(
                f"Request data is invalid for a Schema in "
                f"AllOf({', '.join(type(schema).__name__ for schema in self.schemas)})!"
            ) from e

        conflicting_keys = any(
            schema_loads[schema][shared_key] != schema_loads[schemas[0]][shared_key]
            for shared_key, schemas in self.shared_keys_to_schemas.items()
            for schema in schemas
        )
        if conflicting_keys:
            raise AnyOfConflictError(
                f"Schemas in AnyOf({', '.join(type(schema).__name__ for schema in self.schemas)}) have conflicting keys!"
            )

        return Schema.from_dict({name: field for schema in self.schemas for name, field in schema.fields.items()})()

    def dump(self, obj: Any, *, many: bool = False) -> dict:
        '''TODO: Add docstring for AllOf.dump()'''
        try:
            schema_dumps = {schema: schema.dump(obj, many=False) for schema in self.schemas}
        except ValueError as e:
            raise AllOfValidationError(
                f"'{type(obj).__name__}' is invalid for a Schema in "
                f"AllOf({', '.join(type(schema).__name__ for schema in self.schemas)})!"
            ) from e

        for schema in self.schemas:
            validation_errors = schema.validate(schema_dumps[schema])
            if validation_errors:
                raise AllOfValidationError(
                    f"'{type(obj).__name__}' is invalid for Schema '{type(schema).__name__}' in AllOf!"
                )

        conflicting_keys = any(
            schema_dumps[schema][shared_key] != schema_dumps[schemas[0]][shared_key]
            for shared_key, schemas in self.shared_keys_to_schemas.items()
            for schema in schemas
        )
        if conflicting_keys:
            raise AllOfConflictError(
                f"Schemas in AllOf({', '.join(type(schema).__name__ for schema in self.schemas)}) have conflicting keys!"
            )

        return {k:v for dump in schema_dumps.values() for k,v in dump.items()}
