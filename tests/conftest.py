import pytest
from _pytest.fixtures import SubRequest
from pytest_mock import MockerFixture

from specargs import common

@pytest.fixture
def ensure_schema_or_inpoly(mocker: MockerFixture, request: SubRequest):
    return mocker.patch.object(
        request.module.MODULE_TO_TEST,  # Required in requesting test module
        "ensure_schema_or_inpoly",
        autospec=True,
    )


@pytest.fixture
def ensure_schema_or_inpoly_error(ensure_schema_or_inpoly):
    ensure_schema_or_inpoly.side_effect = TypeError
    return ensure_schema_or_inpoly
