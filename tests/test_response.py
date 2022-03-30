from http import HTTPStatus
from typing import Any

import pytest

from specargs import response


class TestResponse:
    @pytest.mark.parametrize("status_code", (HTTPStatus.NOT_FOUND, 404))
    def test_init(self, status_code: Any):
        data = "data"
        
        result = response.Response(data, status_code)

        assert result.status_code == HTTPStatus.NOT_FOUND
        assert result.data == data
