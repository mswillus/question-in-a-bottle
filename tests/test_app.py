import os

import pytest
from pytest_httpserver import HTTPServer

from ..app import app


@pytest.fixture(scope="function")
def client(httpserver: HTTPServer):
    app.config["PUBLIC_URL"] = httpserver.url_for("")
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_calling_root_returns_404(client):
    rv = client.get("results")
    assert rv.status_code == 404

