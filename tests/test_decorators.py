from collections.abc import Iterable
from http import HTTPStatus

from marshmallow import Schema
import pytest
from _pytest.fixtures import SubRequest
from unittest.mock import MagicMock
from pytest_mock import MockerFixture

from specargs import decorators, OneOf


MODULE_TO_TEST = decorators # Needed for shared pytest mock fixtures in conftest.py


@pytest.fixture
def parser(mocker: MockerFixture):
    default_location = decorators.parser.DEFAULT_LOCATION
    mock = mocker.patch.object(decorators, "parser")

    def decorate(f):
        f.decorated = True
        return f

    inner_decorator_mock = mocker.Mock(side_effect=decorate)
    mock.use_args.return_value = inner_decorator_mock
    mock.DEFAULT_LOCATION = default_location
    return mock


def test_use_args_inpoly_invalid_location():
    with pytest.raises(ValueError):
        decorators.use_args(OneOf(), location="not json")


def test_use_args_invalid_argpoly(ensure_schema_or_inpoly_error: MagicMock):
    with pytest.raises(TypeError):
        decorators.use_args("invalid")(lambda: "WRAP ME!")


@pytest.mark.parametrize("with_location", (
    pytest.param(True, id="With location"),
    pytest.param(False, id="Without location"),
))
def test_use_args(mocker: MockerFixture, parser: MagicMock, with_location: bool):
    argpoly = "argpoly"
    args = ("these", "don't", "matter")
    kwargs = {"also": "really", "don't": "matter"}
    if with_location: kwargs["location"] = "location"
    func = lambda: "WRAP ME!"
    Webargs = mocker.patch.object(decorators, "Webargs", autospec=True)

    func = decorators.use_args(argpoly, *args, **kwargs)(func)

    expected_location = kwargs.pop("location", parser.DEFAULT_LOCATION)
    Webargs.assert_called_once_with(argpoly, expected_location)
    parser.use_args.assert_called_once_with(
        argpoly,
        *args,
        location=expected_location,
        **kwargs
    )
    parser.use_args.return_value.assert_called_once_with(func)
    assert func.decorated
    assert func.webargs == [Webargs.return_value]


def test_use_kwargs(mocker: MockerFixture):
    args = ("these", "don't", "matter")
    kwargs = {"also": "really", "don't": "matter"}
    use_args = mocker.patch.object(decorators, "use_args", autospec=True)

    decorator = decorators.use_kwargs(*args, **kwargs)

    use_args.assert_called_once_with(*args, as_kwargs=True, **kwargs)
    assert decorator == use_args.return_value


@pytest.fixture
def ensure_response(mocker: MockerFixture):
    return mocker.patch.object(decorators, "ensure_response", autospec=True)


def test_use_response_duplicate_response_code(ensure_response: MagicMock):
    func = lambda: "WRAP ME!"
    status_code = 200
    func.responses = {status_code: "response"}

    decorator = decorators.use_response("response_or_argpoly", status_code=status_code)
    with pytest.raises(decorators.DuplicateResponseCodeError):
        decorator(func)


@pytest.mark.parametrize("with_status_code", (
    pytest.param(True, id="With status_code"),
    pytest.param(False, id="Without status_code"),
))
@pytest.mark.parametrize("with_description", (
    pytest.param(True, id="With description"),
    pytest.param(False, id="Without description"),
))
def test_use_response(ensure_response: MagicMock, with_status_code: bool, with_description: bool):
    response_or_argpoly = "response_or_argpoly"
    headers = {"first": "first header", "second": "second header", "third": "third header"}
    func = MagicMock()
    del func.is_resp_wrapper
    del func.responses
    args = ("these", "don't", "matter")
    kwargs = {"also": "really", "don't": "matter"}
    response: MagicMock = ensure_response.return_value
    use_response_kwargs = {}
    if with_status_code: use_response_kwargs["status_code"] = 404
    if with_description: use_response_kwargs["description"] = "a description"
    expected_status_code = use_response_kwargs.get("status_code", 200)

    decorator = decorators.use_response(response_or_argpoly, **use_response_kwargs, **headers)

    ensure_response.assert_called_once_with(
        response_or_argpoly,
        description=use_response_kwargs.get("description", ""),
        headers=headers,
    )

    wrapped_func = decorator(func)

    assert wrapped_func.responses[expected_status_code] == response

    output = wrapped_func(*args, **kwargs)

    func.assert_called_once_with(*args, **kwargs)
    response.dump.assert_called_once_with(func.return_value)
    assert output == (response.dump.return_value, expected_status_code)


def test_use_empty_response(mocker: MockerFixture):
    kwargs = {"these": "really", "don't": "matter"}
    use_response = mocker.patch.object(decorators, "use_response", autospec=True)

    decorator = decorators.use_empty_response(**kwargs)

    use_response.assert_called_once_with(None, **kwargs)
    assert decorator == use_response.return_value
