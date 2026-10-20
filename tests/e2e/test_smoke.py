import os

import httpx
import pytest


@pytest.mark.skipif(not os.environ.get("BASE_URL"), reason="BASE_URL is not set")
def test_health_check_against_deployed_app():
    response = httpx.get(f"{os.environ['BASE_URL']}/health")

    assert response.status_code == 200
