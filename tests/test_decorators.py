from collections.abc import Iterable
from http import HTTPStatus
from typing import Optional, Union

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


@pytest.mark.parametrize("status_code", (
    pytest.param(HTTPStatus.NOT_FOUND),
    pytest.param(404),
    pytest.param(None, id="Without status_code")
))
@pytest.mark.parametrize("with_description", (
    pytest.param(True, id="With description"),
    pytest.param(False, id="Without description"),
))
@pytest.mark.parametrize("already_wrapped", (
    pytest.param(True, id="Previously wrapped"),
    pytest.param(False, id="Not previously wrapped"),
))
def test_use_response(mocker: MockerFixture, ensure_response: MagicMock, status_code: Optional[Union[HTTPStatus, int]], with_description: bool, already_wrapped: bool):
    response_or_argpoly = "response_or_argpoly"
    headers = {"first": "first header", "second": "second header", "third": "third header"}
    func = MagicMock()
    if already_wrapped:
        func.is_resp_wrapper = True
        func.__wrapped__ = MagicMock()
        func.__wrapped__.responses = {}
        func.responses = func.__wrapped__.responses
    else:
        del func.is_resp_wrapper
        del func.responses
    args = ("these", "don't", "matter")
    kwargs = {"also": "really", "don't": "matter"}
    response: MagicMock = ensure_response.return_value
    use_response_kwargs = {}
    if status_code: use_response_kwargs["status_code"] = status_code
    if with_description: use_response_kwargs["description"] = "a description"
    expected_status_code = HTTPStatus(use_response_kwargs.get("status_code", HTTPStatus.OK))
    _get_response_data_and_status = mocker.patch.object(decorators, "_get_response_data_and_status")
    response_data = "response_data"
    _get_response_data_and_status.return_value = (response_data, expected_status_code)
    _dump_response_schema = mocker.patch.object(decorators, "_dump_response_schema")
    make_response = mocker.patch.object(decorators, "make_response")

    decorator = decorators.use_response(response_or_argpoly, **use_response_kwargs, **headers)

    ensure_response.assert_called_once_with(
        response_or_argpoly,
        description=use_response_kwargs.get("description", ""),
        headers=headers,
    )

    wrapped_func = decorator(func)

    if already_wrapped: func = func.__wrapped__

    assert wrapped_func.__wrapped__ == func
    assert wrapped_func.is_resp_wrapper
    assert wrapped_func.responses[expected_status_code] == response

    output = wrapped_func(*args, **kwargs)

    func.assert_called_once_with(*args, **kwargs)
    _get_response_data_and_status.assert_called_once_with(func.return_value, expected_status_code)
    _dump_response_schema(response_data, response.schema)
    make_response.assert_called_once_with(_dump_response_schema.return_value, expected_status_code)
    assert output == make_response.return_value


def test_use_empty_response(mocker: MockerFixture):
    kwargs = {"these": "really", "don't": "matter"}
    use_response = mocker.patch.object(decorators, "use_response", autospec=True)

    decorator = decorators.use_empty_response(**kwargs)

    use_response.assert_called_once_with(None, **kwargs)
    assert decorator == use_response.return_value
