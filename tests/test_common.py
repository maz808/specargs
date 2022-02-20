from marshmallow import fields, Schema
from marshmallow.schema import SchemaMeta
import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock

from apispec_webargs import common


schema_instance = Schema()
schema_factory = lambda: Schema()


@pytest.mark.parametrize("argmap,expected_result", (
    pytest.param(schema_instance, schema_instance, id="Schema instance"),
    pytest.param(schema_factory, schema_factory, id="Schema factory"),
))
def test_ensure_schema_or_factory(argmap, expected_result):
    result = common.ensure_schema_or_factory(argmap)

    assert result == expected_result


def test_ensure_schema_or_factory_schema_class():
    argmap = MagicMock(spec=SchemaMeta)

    result = common.ensure_schema_or_factory(argmap)

    argmap.assert_called_once()
    assert result == argmap.return_value


def test_ensure_schema_or_factory_dict(mocker: MockerFixture):
    argmap = {"test_field": fields.Field()}
    parser = mocker.patch.object(common, "parser", autospec=True)

    result = common.ensure_schema_or_factory(argmap)

    parser.schema_class.from_dict.assert_called_once_with(argmap)
    parser.schema_class.from_dict.return_value.assert_called_once()
    assert result == parser.schema_class.from_dict.return_value.return_value


def test_ensure_schema_or_factory_invalid():
    with pytest.raises(TypeError):
        common.ensure_schema_or_factory("invalid")

