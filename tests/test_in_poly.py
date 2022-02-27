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

    schema_indeces = (0, 1, 2)

    @pytest.mark.parametrize("valid_index", schema_indeces)
    def test_call(self, ensure_schema_or_inpoly: MagicMock, valid_index: int):
        request = MagicMock(spec=Request)
        schemas = tuple(
            MagicMock(spec=Schema, **{"validate.return_value": ("validation_error")})
            for _ in range(len(self.schema_indeces))
        )
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


    @pytest.mark.parametrize("valid_index", schema_indeces)
    def test_dump(self, ensure_schema_or_inpoly: MagicMock, valid_index: int):
        obj = "obj"
        schemas = tuple(
            MagicMock(spec=Schema, **{"validate.return_value": ("validation_error")})
            for _ in range(len(self.schema_indeces))
        )
        valid_schema = schemas[valid_index]
        valid_schema.validate.return_value = ()
        ensure_schema_or_inpoly.side_effect = schemas
        oneof = in_poly.OneOf(*schemas)

        result = oneof.dump(obj)

        for schema in schemas:
            schema.dump.assert_called_once_with(obj)
            schema.validate.assert_called_once_with(schema.dump.return_value)

        assert result == valid_schema.dump.return_value


class TestAnyOf(TestInPoly):
    test_class = in_poly.AnyOf

    @staticmethod
    def test_attrs_post_init(mocker: MockerFixture):
        anyof = in_poly.AnyOf()
        spy = mocker.spy(anyof, "_determine_shared_keys_to_schemas")

        anyof.__attrs_post_init__()

        spy.assert_called_once()

    @staticmethod
    def test_call_validation_error(ensure_schema_or_inpoly: MagicMock):
        request = MagicMock(spec=Request)
        schemas = tuple(
            MagicMock(spec=Schema, fields={"test_field": ""}, **{"load.side_effect": ValidationError("")})
            for _ in range(2)
        )
        ensure_schema_or_inpoly.side_effect = schemas
        anyof = in_poly.AnyOf(*schemas)

        with pytest.raises(in_poly.AnyOfValidationError):
            anyof(request)

    @staticmethod
    def test_call_conflict_error(ensure_schema_or_inpoly: MagicMock):
        request = MagicMock(spec=Request)
        schemas = tuple(
            MagicMock(spec=Schema, fields={"test_field": ""}, **{"load.return_value": {"test_field": x}})
            for x in range(2)
        )
        ensure_schema_or_inpoly.side_effect = schemas
        anyof = in_poly.AnyOf(*schemas)

        with pytest.raises(in_poly.AnyOfConflictError):
            anyof(request)

    @staticmethod
    @pytest.mark.parametrize("multiple", (
        pytest.param(True, id="multiple valid schemas"),
        pytest.param(False, id="single valid schema"),
    ))
    def test_call(mocker: MockerFixture, ensure_schema_or_inpoly: MagicMock, multiple: bool):
        request = MagicMock(spec=Request)
        shared_keys = {"test_field": ""}
        first_schema_fields = {**shared_keys, "first": ""}
        second_schema_fields = {**shared_keys, "second": ""}
        if multiple: second_schema_kwargs = {"load.return_value": second_schema_fields}
        else: second_schema_kwargs = {"load.side_effect": ValidationError("")}
        schemas = (
            MagicMock(spec=Schema, fields=first_schema_fields, **{"load.return_value": first_schema_fields}),
            MagicMock(spec=Schema, fields=second_schema_fields, **second_schema_kwargs),
        )
        ensure_schema_or_inpoly.side_effect = schemas
        schema_class_mock = mocker.patch.object(in_poly, "Schema")
        expected_schema_dict = {**shared_keys, "first": ""}
        if multiple: expected_schema_dict["second"] = ""
        anyof = in_poly.AnyOf(*schemas)

        result = anyof(request)

        for schema in schemas:
            schema.load.assert_called_once_with(request.json, unknown=EXCLUDE)

        schema_class_mock.from_dict.assert_called_once_with(expected_schema_dict)
        schema_class_mock.from_dict.return_value.assert_called_once_with()
        assert result == schema_class_mock.from_dict.return_value.return_value

    @staticmethod
    def test_dump_validation_error(ensure_schema_or_inpoly: MagicMock):
        obj = "obj"
        schemas = (
            MagicMock(spec=Schema, fields={"test_field": ""}, **{"dump.side_effect": ValueError}),
            MagicMock(spec=Schema, fields={"test_field": ""}, **{"validate.return_value": ("validation_error")}),
        )
        ensure_schema_or_inpoly.side_effect = schemas
        anyof = in_poly.AnyOf(*schemas)

        with pytest.raises(in_poly.AnyOfValidationError):
            anyof.dump(obj)

    @staticmethod
    def test_dump_conflict_error(ensure_schema_or_inpoly: MagicMock):
        obj = "obj"
        schemas = tuple(
            MagicMock(spec=Schema, fields={"test_field": ""}, **{"dump.return_value": {"test_field": x}})
            for x in range(2)
        )
        ensure_schema_or_inpoly.side_effect = schemas
        anyof = in_poly.AnyOf(*schemas)

        with pytest.raises(in_poly.AnyOfConflictError):
            anyof.dump(obj)

    @staticmethod
    @pytest.mark.parametrize("multiple", (
        pytest.param(True, id="multiple valid schemas"),
        pytest.param(False, id="single valid schema"),
    ))
    def test_dump(ensure_schema_or_inpoly: MagicMock, multiple: bool):
        obj = "obj"
        shared_keys = {"test_field": ""}
        first_schema_fields = {**shared_keys, "first": ""}
        second_schema_fields = {**shared_keys, "second": ""}
        # To make sure invalid schemas are excluded from conflicting keys check
        invalid_schema_fields = {"test_field": "invalid", "third": ""}
        if multiple: second_schema_kwargs = {"dump.return_value": second_schema_fields}
        else: second_schema_kwargs = {"dump.side_effect": ValueError}
        schemas = (
            MagicMock(spec=Schema, fields=first_schema_fields, **{"dump.return_value": first_schema_fields}),
            MagicMock(spec=Schema, fields=second_schema_fields, **second_schema_kwargs),
            MagicMock(spec=Schema, fields=invalid_schema_fields, **{"dump.side_effect": ValueError})
        )
        ensure_schema_or_inpoly.side_effect = schemas
        expected_result = {**shared_keys, "first": ""}
        if multiple: expected_result["second"] = ""
        anyof = in_poly.AnyOf(*schemas)

        result = anyof.dump(obj)

        for schema in schemas:
            schema.dump.assert_called_once_with(obj)

        schemas[0].validate.assert_called_once_with(schemas[0].dump.return_value)
        if multiple: schemas[1].validate.assert_called_once_with(schemas[1].dump.return_value)
        assert result == expected_result


class TestAllOf(TestInPoly):
    test_class = in_poly.AllOf

    @staticmethod
    def test_attrs_post_init(mocker: MockerFixture):
        allof = in_poly.AllOf()
        spy = mocker.spy(allof, "_determine_shared_keys_to_schemas")

        allof.__attrs_post_init__()

        spy.assert_called_once()

    @staticmethod
    def test_call_validation_error(ensure_schema_or_inpoly: MagicMock):
        request = MagicMock(spec=Request)
        schemas = tuple(
            MagicMock(spec=Schema, fields={"test_field": ""}, **{"load.return_value": {"test_field": ""}})
            for _ in range(3)
        )
        schemas[-1].load.side_effect = ValidationError("")
        ensure_schema_or_inpoly.side_effect = schemas
        allof = in_poly.AllOf(*schemas)

        with pytest.raises(in_poly.AllOfValidationError):
            allof(request)

    @staticmethod
    def test_call_conflict_error(ensure_schema_or_inpoly: MagicMock):
        request = MagicMock(spec=Request)
        schemas = tuple(
            MagicMock(spec=Schema, fields={"test_field": ""}, **{"load.return_value": {"test_field": x}})
            for x in range(2)
        )
        ensure_schema_or_inpoly.side_effect = schemas
        allof = in_poly.AllOf(*schemas)

        with pytest.raises(in_poly.AllOfConflictError):
            allof(request)

    @staticmethod
    def test_call(mocker: MockerFixture, ensure_schema_or_inpoly: MagicMock):
        request = MagicMock(spec=Request)
        shared_keys = {"test_field": ""}
        first_schema_fields = {**shared_keys, "first": ""}
        second_schema_fields = {**shared_keys, "second": ""}
        schemas = (
            MagicMock(spec=Schema, fields=first_schema_fields, **{"load.return_value": first_schema_fields}),
            MagicMock(spec=Schema, fields=second_schema_fields, **{"load.return_value": second_schema_fields}),
        )
        ensure_schema_or_inpoly.side_effect = schemas
        schema_class_mock = mocker.patch.object(in_poly, "Schema")
        expected_schema_dict = {**first_schema_fields, **second_schema_fields}
        allof = in_poly.AllOf(*schemas)

        result = allof(request)

        for schema in schemas:
            schema.load.assert_called_once_with(request.json, unknown=EXCLUDE)

        schema_class_mock.from_dict.assert_called_once_with(expected_schema_dict)
        schema_class_mock.from_dict.return_value.assert_called_once_with()
        assert result == schema_class_mock.from_dict.return_value.return_value

    @staticmethod
    @pytest.mark.parametrize("cause", ("dump", "validate"))
    def test_dump_validation_error(ensure_schema_or_inpoly: MagicMock, cause: str):
        obj = "obj"
        schema_kwargs = {"dump.return_value": {"test_field": ""}, "validate.return_value": ()}
        schemas = tuple(
            MagicMock(spec=Schema, fields={"test_field": ""}, **schema_kwargs)
            for _ in range(2)
        )
        if cause == "dump": schemas[-1].dump.side_effect = ValueError
        if cause == "validate": schemas[-1].validate.return_value = ("validation_error")
        ensure_schema_or_inpoly.side_effect = schemas
        allof = in_poly.AllOf(*schemas)

        with pytest.raises(in_poly.AllOfValidationError):
            allof.dump(obj)

    @staticmethod
    def test_dump_conflict_error(ensure_schema_or_inpoly: MagicMock):
        obj = "obj"
        schemas = tuple(
            MagicMock(
                spec=Schema,
                fields={"test_field": ""},
                **{"validate.return_value": (), "dump.return_value": {"test_field": x}}
            ) for x in range(2)
        )
        ensure_schema_or_inpoly.side_effect = schemas
        allof = in_poly.AllOf(*schemas)

        with pytest.raises(in_poly.AllOfConflictError):
            allof.dump(obj)

    @staticmethod
    def test_dump(ensure_schema_or_inpoly: MagicMock):
        obj = "obj"
        shared_keys = {"test_field": ""}
        first_schema_fields = {**shared_keys, "first": ""}
        second_schema_fields = {**shared_keys, "second": ""}
        schemas = (
            MagicMock(spec=Schema, fields=first_schema_fields, **{"dump.return_value": first_schema_fields}),
            MagicMock(spec=Schema, fields=second_schema_fields, **{"dump.return_value": second_schema_fields}),
        )
        for schema in schemas: schema.validate.return_value = ()
        ensure_schema_or_inpoly.side_effect = schemas
        expected_result = {**first_schema_fields, **second_schema_fields}
        allof = in_poly.AllOf(*schemas)

        result = allof.dump(obj)

        for schema in schemas:
            schema.dump.assert_called_once_with(obj, many = False)
            schema.validate.assert_called_once_with(schema.dump.return_value)

        assert result == expected_result
