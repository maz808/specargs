from marshmallow import fields, Schema
import pytest
from unittest.mock import MagicMock

from specargs import common, OneOf


MODULE_TO_TEST = common


class TestWebargs:
    @staticmethod
    def test_init_error(ensure_schema_or_inpoly_error: MagicMock):
        with pytest.raises(TypeError):
            common.Webargs("argpoly", "location")

    @staticmethod
    def test_init(ensure_schema_or_inpoly: MagicMock):
        argpoly = "argpoly"
        location = "location"

        webargs = common.Webargs(argpoly, location)

        ensure_schema_or_inpoly.assert_called_once_with(argpoly)
        assert webargs.schema_or_inpoly == ensure_schema_or_inpoly.return_value
        assert webargs.location == location


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


class SchemaForTests(Schema):
    pass


def test_ensure_schema_or_inpoly_schema_class():
    result = common.ensure_schema_or_inpoly(SchemaForTests)
    assert isinstance(result, SchemaForTests)


@pytest.mark.parametrize("invalid", (
    pytest.param((lambda: "invalid"), id="Invalid callable"),
    pytest.param("invalid", id="Invalid type"),
))
def test_ensure_schema_or_inpoly_invalid(invalid):
    with pytest.raises(TypeError):
        common.ensure_schema_or_inpoly(invalid)
