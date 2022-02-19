from collections.abc import Iterable

import pytest
from _pytest.fixtures import SubRequest
from unittest.mock import MagicMock
from pytest_mock import MockerFixture

from apispec_webargs import decorators, OneOf


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


def test_use_args_schema_factory_error():
    with pytest.raises(TypeError):
        decorators.use_args(lambda: "NOT ALLOWED")


def test_use_args_inpoly_invalid_location():
    with pytest.raises(ValueError):
        decorators.use_args(OneOf(), location="not json")


@pytest.mark.parametrize("with_location", (
    pytest.param(True, id="With location"),
    pytest.param(False, id="Without location"),
))
def test_use_args(parser: MagicMock, with_location: bool):
    argmap = "argmap"
    args = ("these", "don't", "matter")
    kwargs = {"also": "really", "don't": "matter"}
    if with_location: kwargs["location"] = "location"
    func = lambda: "WRAP ME!"

    func = decorators.use_args(argmap, *args, **kwargs)(func)

    expected_location = kwargs.pop("location", parser.DEFAULT_LOCATION)

    parser.use_args.assert_called_once_with(argmap, *args, location=expected_location, **kwargs)
    parser.use_args.return_value.assert_called_once_with(func)
    assert func.decorated
    assert func.webargs == [decorators.Webargs(argmap, expected_location)]


def test_use_kwargs(mocker: MockerFixture):
    args = ("these", "don't", "matter")
    kwargs = {"also": "really", "don't": "matter"}
    use_args = mocker.patch.object(decorators, "use_args", autospec=True)

    decorator = decorators.use_kwargs(*args, **kwargs)

    use_args.assert_called_once_with(*args, as_kwargs=True, **kwargs)
    assert decorator == use_args.return_value


@pytest.fixture(params=(
    pytest.param(True, id="response.schema True"),
    pytest.param(False, id="response.schema False"),
))
def ensure_response(mocker: MockerFixture, request: SubRequest):
    mock = mocker.patch.object(decorators, "ensure_response", autospec=True)
    if not(request.param): mock.return_value.schema = None
    return mock


def test_use_response_duplicate_response_code(ensure_response: MagicMock):
    func = lambda: "WRAP ME!"
    status_code = 200
    func.responses = {status_code: "response"}

    decorator = decorators.use_response("response_or_argmap", status_code=status_code)
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
    response_or_argmap = None
    headers = {"first": "first header", "second": "second header", "third": "third header"}
    func = lambda *args, **kwargs: (args, kwargs)
    args = ("these", "don't", "matter")
    kwargs = {"also": "really", "don't": "matter"}
    func_return = func(*args, **kwargs)
    response: MagicMock = ensure_response.return_value
    use_response_kwargs = {}
    if with_status_code: use_response_kwargs["status_code"] = 418
    if with_description: use_response_kwargs["description"] = "a description"
    expected_status_code = use_response_kwargs.get("status_code", 200)

    decorator = decorators.use_response(response_or_argmap, **use_response_kwargs, **headers)

    ensure_response.assert_called_once_with(
        response_or_argmap,
        description=use_response_kwargs.get("description", ""),
        headers=headers,
    )

    wrapped_func = decorator(func)

    assert wrapped_func.responses[expected_status_code] == response

    output = wrapped_func(*args, **kwargs)

    expected_value = ""
    if response.schema:
        response.schema.dump.assert_called_once_with(func_return, many=isinstance(func_return, Iterable))
        expected_value = response.schema.dump.return_value

    assert output == (expected_value, expected_status_code)


def test_use_empty_response(mocker: MockerFixture):
    kwargs = {"these": "really", "don't": "matter"}
    use_response = mocker.patch.object(decorators, "use_response", autospec=True)

    decorator = decorators.use_empty_response(**kwargs)

    use_response.assert_called_once_with(None, **kwargs)
    assert decorator == use_response.return_value
