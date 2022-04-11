from abc import ABC, abstractclassmethod, abstractmethod
import json
from typing import Any, ClassVar, Tuple

from attrs import define, field
from marshmallow import Schema, EXCLUDE, ValidationError

from .common import ensure_schema_or_inpoly, con, ArgMap
from .framework import get_request_body


@define
class InPoly(ABC):
    '''An abstract representation of the inheritance/polymorphism keywords of the OpenAPI Specification

    Subclasses of this class not only enable generation of correpsonding OpenAPI Specification clauses, but also data
    deserialization when provided to :func:`~specargs.use_args` or :func:`~specargs.use_kwargs` and data
    serialization when provided to :func:`~specargs.use_response`.
    '''
    #: The marshmallow `Schema` instances that will be converted into members of the keyword and determine serialization and deserialization behavior
    schemas: Tuple[Schema] = field(converter=lambda objs: tuple(map(ensure_schema_or_inpoly, objs)))

    def __init__(self, *argmaps: ArgMap):
        '''Initializes an :class:`InPoly` instance

        Args:
            *argmaps: Dictionaries of marshmallow `Field` instances or marshmallow `Schema` instances or classes
                provided as positional arguments. Converted into `Schema` instances and stored in :attr:`~specargs.in_poly.InPoly.schemas`

        Raises:
            :exc:`TypeError`: If any of the provided `argmaps` are :class:`~specargs.in_poly.InPoly` objects
        '''
        # TODO: Add support for nested `InPoly` objects
        if any(isinstance(schema, InPoly) for schema in argmaps):
            raise TypeError("Nested `InPoly` objects are not currently supported!")
        self.__attrs_init__(argmaps)

    def __attrs_post_init__(self):
        pass

    def _determine_shared_keys_to_schemas(self):
        keys_to_schemas = {}
        for schema in self.schemas:
            for key in schema.fields.keys():
                keys_to_schemas[key] = (*keys_to_schemas.get(key, ()), schema)

        self.shared_keys_to_schemas = {key: schemas for key, schemas in keys_to_schemas.items() if len(schemas) > 1}

    @property
    @abstractclassmethod
    def keyword(cls) -> str:
        '''The OpenAPI Spec keyword assigned to the class'''
        ...  # pragma: no cover

    @abstractmethod
    def dump(self, obj: Any, *, many: bool = False) -> dict:
        '''Serializes the given object into a dictionary

        This method mimics the behavior of the :meth:`marshmallow.Schema.dump` method
        '''
        ...  # pragma: no cover

    @abstractmethod
    def __call__(self, request: Any) -> Schema:
        ...  # pragma: no cover


con.register_unstructure_hook(InPoly, lambda ip: {ip.keyword: ip.schemas})


# TODO: Improve initialization of OneOfConflictError (args to generate message)
class OneOfConflictError(Exception):
    '''An exception for :class:`OneOf` serlialization/deserialization conflicts

    This is raised when data that is being serialized or deserialized by a :class:`OneOf` instance is valid for
    multiple :attr:`~InPoly.schemas` of that instance.
    '''
    pass


# TODO: Improve initialization of OneOfValidationError (args to generate message)
class OneOfValidationError(Exception):
    '''An exception for :class:`OneOf` validation

    This is raised when data that is being serialized or deserialized by a :class:`OneOf` instance is invalid for
    all :attr:`~InPoly.schemas` of that instance.
    '''
    pass


class OneOf(InPoly):
    '''A representation of the 'oneOf' OpenAPI Specification keyword'''
    keyword: ClassVar[str] = "oneOf"

    def __init__(self, *argmaps: ArgMap, unknown: str = EXCLUDE):
        '''Initializes a :class:`OneOf` instance

        Args:
            *argmaps: Dictionaries of :mod:`marshmallow.fields` or :class:`marshmallow.Schema` instances or classes
                provided as positional arguments. Converted into :class:`marshmallow.Schema` instances and stored in
                :attr:`in_poly.InPoly.schemas`
            unknown: Determines the behavior of unknown fields when serializing/deserializing. Defaults to
                :const:`marshmallow.utils.EXCLUDE`

        Raises:
            :The same exceptions as :meth:`in_poly.InPoly.__init__` for the same reasons
        '''
        super().__init__(*argmaps)
        for schema in self.schemas:
            schema.unknown = unknown

    def __call__(self, request: Any) -> Schema:
        '''Generates a :class:`marshmallow.Schema` based on the given request object

        Args:
            request: The request object which holds the data used to produce the :class:`marshmallow.Schema`

        Returns:
            The single :class:`marshmallow.Schema` from :attr:`OneOf.schemas` that successfully validates the request
            data

        Raises:
            :exc:`OneOfConflictError`: If more than one of :attr:`OneOf.schemas` succesfully validates the request data
            :exc:`OneOfValidationError`: If none of :attr:`OneOf.schemas` succesfully validate the request data
        '''
        # TODO: Determine Request type based on framework
        valid_schemas = tuple(schema for schema in self.schemas if len(schema.validate(get_request_body(request))) == 0)
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

    # TODO: Add argument entry for `many` kwarg
    def dump(self, obj: Any, *, many: bool = False) -> dict:
        '''Serializes the given object into a dictionary

        This method mimics the behavior of marshmallow's `Schema.dump` method

        Args:
            obj: The object to serialize

        Returns:
            The object serialization output of one of the :attr:`OneOf.schemas`

        Raises:
            :exc:`OneOfConflictError`: If more than one of :attr:`OneOf.schemas` succesfully validates the object
            :exc:`OneOfValidationError`: If none of :attr:`OneOf.schemas` succesfully validate the object
        '''
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
    '''An exception for :class:`AnyOf` validation

    This is raised when an object being serialized/deserialized by an :class:`AnyOf` is invalid for all
    :attr:`~InPoly.schemas` of that instance.
    '''
    pass


# TODO: Improve initialization of AnyOfConflictError (args to generate message)
class AnyOfConflictError(Exception):
    '''An exception for :class:`AnyOf` serlialization/deserialization conflicts

    This is raised when the :attr:`~InPoly.schemas` of an :class:`AnyOf` instance produce keys with conflicting values
    on serialization or deserialization.
    '''
    pass


class AnyOf(InPoly):
    '''A representation of the 'anyOf' OpenAPI Spec keyword'''
    keyword: ClassVar[str] = "anyOf"

    def __attrs_post_init__(self):
        self._determine_shared_keys_to_schemas()

    def __call__(self, request: Any) -> Schema:
        '''Generates a marshmallow `Schema` based on the given request object

        Args:
            request: The request object which holds the data used to produce the `Schema`

        Returns:
            A `Schema` that's a combination of all :attr:`AnyOf.schemas` that successfully validate the request data

        Raises:
            :exc:`AnyOfConflictError`: If the :attr:`AnyOf.schemas` that succesfully validate the request data produce
                differing values for a given key
            :exc:`AnyOfValidationError`: If none of :attr:`AnyOf.schemas` succesfully validate the request data
        '''
        valid_schema_loads = {}
        for schema in self.schemas:
            try: load = schema.load(get_request_body(request), unknown=EXCLUDE)
            except ValidationError: continue
            if not isinstance(load, dict):
                load = vars(load) if hasattr(load, "__dict__") else {s: getattr(load, s, None) for s in load.__slots__}

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
        '''Serializes the given object into a dictionary

        This method mimics the behavior of marshmallow's `Schema.dump` method

        Args:
            obj: The object to serialize

        Returns:
            The object serialization output of all of the :attr:`AnyOf.schemas` that successfully validate the object

        Raises:
            :exc:`AnyOfConflictError`: If the :attr:`AnyOf.schemas` that succesfully validate the object produce
                differing values for a given key
            :exc:`AnyOfValidationError`: If none of :attr:`AnyOf.schemas` succesfully validate the object
        '''
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
    '''An exception for :class:`AllOf` serlialization/deserialization conflicts

    This is raised when the :attr:`~InPoly.schemas` of an :class:`AllOf` instance produce keys with conflicting values
    on serialization or deserialization.
    '''
    pass


# TODO: Improve initialization of AllOfValidationError (args to generate message)
class AllOfValidationError(Exception):
    '''An exception for :class:`AllOf` validation

    This is raised when an object being serialized/deserialized by an :class:`AllOf` is invalid for all
    :attr:`~InPoly.schemas` of that instance.
    '''
    pass


class AllOf(InPoly):
    '''A representation of the 'allOf' OpenAPI Spec keyword'''
    keyword: ClassVar[str] = "allOf"

    def __attrs_post_init__(self):
        self._determine_shared_keys_to_schemas()

    def __call__(self, request: Any) -> Schema:
        '''Generates a marshmallow `Schema` based on the given request object

        Args:
            request: The request object which holds the data used to produce the `Schema`

        Returns:
            A `Schema` that's a combination of all :attr:`AllOf.schemas`

        Raises:
            :exc:`AllOfConflictError`: If the :attr:`AllOf.schemas` produce differing values for a given key
            :exc:`AllOfValidationError`: If any of :attr:`AllOf.schemas` don't succesfully validate the request data
        '''
        try:
            schema_loads = {}
            for schema in self.schemas:
                load = schema.load(get_request_body(request), unknown=EXCLUDE)
                if not isinstance(load, dict):
                    load = (
                        vars(load) if hasattr(load, "__dict__") else
                        {s: getattr(load, s, None) for s in load.__slots__}
                    )
                schema_loads[schema] = load
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
            raise AllOfConflictError(
                f"Schemas in AllOf({', '.join(type(schema).__name__ for schema in self.schemas)}) have conflicting keys!"
            )

        return Schema.from_dict({name: field for schema in self.schemas for name, field in schema.fields.items()})()

    def dump(self, obj: Any, *, many: bool = False) -> dict:
        '''Serializes the given object into a dictionary

        This method mimics the behavior of marshmallow's `Schema.dump` method

        Args:
            obj: The object to serialize

        Returns:
            The combined object serialization output of all of the :attr:`AllOf.schemas`

        Raises:
            :exc:`AllOfConflictError`: If the :attr:`AllOf.schemas` that succesfully validate the object produce
                differing values for a given key
            :exc:`AllOfValidationError`: If none of :attr:`AllOf.schemas` succesfully validate the object
        '''
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
