from marshmallow import fields, Schema
import pytest

from apispec_webargs import common, OneOf


@pytest.mark.parametrize("obj", (
    pytest.param(Schema(), id="Schema instance"),
    pytest.param(OneOf(), id="InPoly instance"),
))
def test_ensure_schema_or_inpoly_immediate_return(obj):
    result = common.ensure_schema_or_inpoly(obj)

    assert result == obj


def test_ensure_schema_or_inpoly_dict():
    obj = {"test_field": fields.Field()}

    result = common.ensure_schema_or_inpoly(obj)

    assert isinstance(result, Schema)
    assert obj.keys() == result.fields.keys()
    assert all(repr(obj[field_name]) == repr(result.fields[field_name]) for field_name in obj)


class TestSchema(Schema):
    pass


def _test_schema_factory():
    return TestSchema()


@pytest.mark.parametrize("schema_class_or_factory", (
    pytest.param(TestSchema, id="Schema class"),
    pytest.param(_test_schema_factory, id="Schema factory"),
))
def test_ensure_schema_or_inpoly_schema_class(schema_class_or_factory):
    result = common.ensure_schema_or_inpoly(schema_class_or_factory)
    assert isinstance(result, TestSchema)


@pytest.mark.parametrize("invalid", (
    pytest.param((lambda x: Schema()), id="Invalid Schema factory"),
    pytest.param((lambda: "invalid"), id="Invalid callable"),
    pytest.param("invalid", id="Invalid type"),
))
def test_ensure_schema_or_inpoly_invalid(invalid):
    with pytest.raises(TypeError):
        common.ensure_schema_or_inpoly(invalid)
