from marshmallow import fields, Schema
from marshmallow.schema import SchemaMeta
import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock

from apispec_webargs import common, OneOf


@pytest.mark.parametrize("obj", (
    pytest.param(Schema(), id="Schema instance"),
    pytest.param(OneOf(), id="InPoly instance"),
))
def test_ensure_schema_or_inpoly_immediate_return(obj):
    result = common.ensure_schema_or_inpoly(obj)

    assert result == obj


class TestSchema(Schema):
    pass


def test_ensure_schema_or_inpoly_schema_class():
    result = common.ensure_schema_or_inpoly(TestSchema)

    assert isinstance(result, TestSchema)


def test_ensure_schema_or_inpoly_dict():
    obj = {"test_field": fields.Field()}

    result = common.ensure_schema_or_inpoly(obj)

    assert isinstance(result, Schema)
    assert obj.keys() == result.fields.keys()
    assert all(repr(obj[field_name]) == repr(result.fields[field_name]) for field_name in obj)


def test_ensure_schema_or_inpoly_invalid():
    with pytest.raises(TypeError):
        common.ensure_schema_or_inpoly("invalid")

