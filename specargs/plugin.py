from abc import ABC
import math
from typing import Dict, Union, List, TYPE_CHECKING

from apispec.ext.marshmallow import MarshmallowPlugin, SchemaResolver
from marshmallow import Schema
from webargs import fields

from .common import con, Webargs
from .validate import MultipleOf

if TYPE_CHECKING:
    from .oas import Response
    from .in_poly import InPoly
else:
    Response = "Response"
    InPoly = "InPoly"


def field2multipleOf(_, field, **kwargs):
    """Return the dictionary of OpenAPI field attributes for a set of
    :class:`MultipleOf <specargs.MultipleOf>` validators.

    :param Field field: A marshmallow field.
    :rtype: dict
    """
    validators = [
        validator
        for validator in field.validators
        if isinstance(validator, MultipleOf)
    ]
    if not validators: return {}
    # Remove any validator values that are a factor of any of the other validator values
    # TODO: Log suggestion to remove values found to be factors
    relevant_values = (
        validator.multiply for validator in validators for other_validator in validators
        if not any(other_validator.multiply % validator.multiply == 0)
    )
    return {"multipleOf": math.prod(relevant_values)}


class WebargsScehamResolver(SchemaResolver):
    '''The same as `apispec.ext.marshmallow.SchemaResolver` with additions for marshmallow Field conversion'''
    def resolve_schema_dict(self, schema):
        '''The same as the superclass method but with a check for marshmallow Fields
        
        The marshmallow Field check enables conversion of marhsmallow Field objects to corresponding OpenAPI Spec
        structures within response sections

        Args:
            schema: The object to be resolved/converted into an OAS structure

        Returns:
            The object after conversion/resolution
        '''
        if isinstance(schema, fields.Field):
            return self.converter.field2property(schema)
        return super().resolve_schema_dict(schema)


class WebargsPlugin(MarshmallowPlugin, ABC):
    '''Generates OpenAPI specification components from decorated view functions/methods
    
    An instance of this class should be given to an instance of :class:`~specargs.WebargsAPISpec` in order for
    an OpenAPI spec to be generated from decorated view functions/methods. This class does not need to be interacted
    with otherwise.
    '''
    Resolver = WebargsScehamResolver

    def __init__(self):
        # Pass in lambda that returns None to completely disable schema name resolution. References to a Schema should
        # only be resolvable if the Schema has been registered in the spec using `APISpec.components.schema`
        super().__init__(schema_name_resolver=lambda _: None)
        self.response_refs: Dict[Response, str] = {}

    def init_spec(self, spec):
        super().init_spec(spec)
        self.converter.add_attribute_function(field2multipleOf)

    def response_helper(self, _, *, response: Response, **kwargs):
        return super().response_helper(con.unstructure(response))

    def _content_from_schema_or_inpoly(self, schema_or_inpoly: Union[Schema, InPoly]) -> dict:
        from .in_poly import InPoly
        if isinstance(schema_or_inpoly, InPoly): schema_or_inpoly = con.unstructure(schema_or_inpoly)
        return {
            "content": {
                "application/json": {
                    "schema": self.resolver.resolve_schema_dict(schema_or_inpoly)
                }
            }
        }

    def _request_body_from_schema_or_inpoly(self, schema_or_inpoly: Union[Schema, InPoly]) -> dict:
        request_body_dict = {"required": True}
        request_body_dict.update(self._content_from_schema_or_inpoly(schema_or_inpoly))
        return {"requestBody": request_body_dict}

    def _operation_input_data_from_webargs(self, webargs: Webargs):
        return (self._request_body_from_schema_or_inpoly(webargs.schema_or_inpoly) if webargs.location == "json" else
            {"parameters": self.converter.schema2parameters(webargs.schema_or_inpoly, location=webargs.location)})

    def _operation_output_data_from_response(self, response: Response):
        response_id = self.spec.response_refs.get(response)
        if response_id: return response_id
        response_dict: dict = con.unstructure(response)
        if "content" in response_dict: self.resolver.resolve_response(response_dict)
        return response_dict

    def _update_operations(self, operations, *, view, method_name: str):
        operations.setdefault(method_name, {})
        for webargs in getattr(view, "webargs", ()):
            if not isinstance(webargs, Webargs):
                raise TypeError("The webargs attribute should be a list of only decorators.Webargs!")
            operations[method_name].update(
                self._operation_input_data_from_webargs(webargs)
            )

        responses = {
            status_code.value: self._operation_output_data_from_response(response)
            for status_code, response in getattr(view, "responses", {}).items()
        }
        if responses: operations[method_name]["responses"] = responses
