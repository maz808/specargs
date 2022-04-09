from http import HTTPStatus
from typing import Any

import pytest

from specargs import view_response


class TestViewResponse:
    @pytest.mark.parametrize("status_code", (HTTPStatus.NOT_FOUND, 404))
    def test_init(self, status_code: Any):
        data = "data"
        
        result = view_response.ViewResponse(data, status_code)

        assert result.status_code == HTTPStatus.NOT_FOUND
        assert result.data == data
