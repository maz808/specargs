import pytest
from _pytest.fixtures import SubRequest
from pytest_mock import MockerFixture


def _create_mock(mocker: MockerFixture, request: SubRequest, name: str):
    return mocker.patch.object(
        request.module.MODULE_TO_TEST,  # Required in requesting test module
        name,
        autospec=True,
    )


@pytest.fixture
def ensure_schema_or_inpoly(mocker: MockerFixture, request: SubRequest):
    return _create_mock(
        mocker,
        request, 
        "ensure_schema_or_inpoly",
    )


@pytest.fixture
def ensure_schema_or_inpoly_error(ensure_schema_or_inpoly):
    ensure_schema_or_inpoly.side_effect = TypeError
    return ensure_schema_or_inpoly


@pytest.fixture
def make_response(mocker: MockerFixture, request: SubRequest):
    return _create_mock(
        mocker,
        request, 
        "make_response",
    )
