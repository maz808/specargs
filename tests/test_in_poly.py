from typing import ClassVar, Tuple

from unittest.mock import call, MagicMock
from marshmallow import Schema, fields, EXCLUDE, ValidationError
import pytest
from pytest_mock import MockerFixture

from apispec_webargs import in_poly
from apispec_webargs.common import con

from flask import Request


MODULE_TO_TEST = in_poly


class InPolyTestSubclass(in_poly.InPoly):
    keyword: ClassVar[str] = "test"

    def dump(self):
        pass

    def __call__(self):
        pass


@pytest.mark.usefixtures("ensure_schema_or_inpoly")
class TestInPoly:
    test_class = InPolyTestSubclass

    def test_init_nested_inpoly_error(self):
        argmaps = (Schema, self.test_class(Schema()))

        with pytest.raises(TypeError):
            self.test_class(*argmaps)

    def test_init_invalid_argpoly(self, ensure_schema_or_inpoly_error: MagicMock):
        with pytest.raises(TypeError):
            self.test_class("not important")

    def test_init_and_unstructure(self, ensure_schema_or_inpoly: MagicMock, **kwargs):
        schemas = tuple(MagicMock(spec=Schema, fields={"test_field": ""}) for _ in range(3))
        ensure_schema_or_inpoly.side_effect = schemas

        inpoly = self.test_class(*schemas, **kwargs)

        ensure_schema_or_inpoly.assert_has_calls(calls=map(call, schemas))
        assert inpoly.schemas == schemas
        assert con.unstructure(inpoly) == {inpoly.keyword: schemas}
        return inpoly

    @pytest.mark.parametrize("input_fields_list,expected_shared_key_indeces", (
        (
            (
                {"one", "two", "three"},
                {"two", "four", "five"},
                {"two", "three"},
                {"five", "six"},
            ),
            {"two": (0, 1, 2), "three": (0, 2), "five": (1, 3)}
        ),
        (
            (
                {"one", "two", "three"},
                {"four", "five"},
                {"six", "seven"},
            ),
            {}
        )
    ))
    def test_determine_shared_keys_to_schemas(
        self,
        ensure_schema_or_inpoly: MagicMock,
        input_fields_list: Tuple[dict],
        expected_shared_key_indeces: dict,
    ):
        ensure_schema_or_inpoly.side_effect = tuple(
            MagicMock(spec=Schema, fields={field: "" for field in input_fields}) for input_fields in input_fields_list
        )
        inpoly = self.test_class(*input_fields_list)
        expected_shared_keys_to_schemas = {
            key: tuple(inpoly.schemas[i] for i in indeces)
            for key, indeces in expected_shared_key_indeces.items()
        }

        inpoly._determine_shared_keys_to_schemas()

        assert inpoly.shared_keys_to_schemas == expected_shared_keys_to_schemas


class TestOneOf(TestInPoly):
    test_class = in_poly.OneOf

    @pytest.mark.parametrize("with_unknown", (
        pytest.param(True, id="With unknown"),
        pytest.param(False, id="Without unknown")
    ))
    def test_init_and_unstructure(self, ensure_schema_or_inpoly, with_unknown):
        unknown = "unknown"
        kwargs = {}
        if with_unknown:
            kwargs["unknown"] = unknown
        expected_unknown = kwargs.get("unknown", EXCLUDE)

        oneof = super().test_init_and_unstructure(ensure_schema_or_inpoly, **kwargs)

        assert all(schema.unknown == expected_unknown for schema in oneof.schemas)

    @staticmethod
    def test_call_conflict_error(ensure_schema_or_inpoly):
        request = MagicMock(spec=Request)
        schemas = tuple(MagicMock(spec=Schema, **{"validate.return_value": ()}) for _ in range(2))
        ensure_schema_or_inpoly.side_effect = schemas
        oneof = in_poly.OneOf(*schemas)

        with pytest.raises(in_poly.OneOfConflictError):
            oneof(request)

    @staticmethod
    def test_call_validation_error(ensure_schema_or_inpoly):
        request = MagicMock(spec=Request)
        schemas = tuple(MagicMock(spec=Schema, **{"validate.return_value": ("validation_error")}) for _ in range(2))
        ensure_schema_or_inpoly.side_effect = schemas
        oneof = in_poly.OneOf(*schemas)

        with pytest.raises(in_poly.OneOfValidationError):
            oneof(request)

    @staticmethod
    @pytest.mark.parametrize("valid_index", (0, 1, 2))
    def test_call(ensure_schema_or_inpoly: MagicMock, valid_index: int):
        request = MagicMock(spec=Request)
        schemas = tuple(MagicMock(spec=Schema, **{"validate.return_value": ("validation_error")}) for _ in range(3))
        valid_schema = schemas[valid_index]
        valid_schema.validate.return_value = ()
        ensure_schema_or_inpoly.side_effect = schemas
        oneof = in_poly.OneOf(*schemas)

        result = oneof(request)

        for schema in schemas:
            schema.validate.assert_called_once_with(request.json)
        
        assert result == valid_schema

    @staticmethod
    def test_dump_conflict_error(ensure_schema_or_inpoly: MagicMock):
        obj = "obj"
        schemas = tuple(MagicMock(spec=Schema) for _ in range(2))
        ensure_schema_or_inpoly.side_effect = schemas
        oneof = in_poly.OneOf(*schemas)

        with pytest.raises(in_poly.OneOfConflictError):
            oneof.dump(obj)

    @staticmethod
    def test_dump_validation_error(ensure_schema_or_inpoly: MagicMock):
        obj = "obj"
        schemas = (
            MagicMock(spec=Schema, **{"dump.side_effect": ValueError}),
            MagicMock(spec=Schema, **{"validate.return_value": ("validation_error")}),
        )
        ensure_schema_or_inpoly.side_effect = schemas
        oneof = in_poly.OneOf(*schemas)

        with pytest.raises(in_poly.OneOfValidationError):
            oneof.dump(obj)

    @staticmethod
    @pytest.mark.parametrize("valid_index", (0, 1, 2))
    def test_dump(ensure_schema_or_inpoly: MagicMock, valid_index: int):
        obj = "obj"
        schemas = tuple(MagicMock(spec=Schema, **{"validate.return_value": ("validation_error")}) for _ in range(3))
        valid_schema = schemas[valid_index]
        valid_schema.validate.return_value = ()
        ensure_schema_or_inpoly.side_effect = schemas
        oneof = in_poly.OneOf(*schemas)

        result = oneof.dump(obj)

        for schema in schemas:
            schema.dump.assert_called_once_with(obj)
            schema.validate.assert_called_once_with(schema.dump.return_value)

        assert result == valid_schema.dump.return_value
