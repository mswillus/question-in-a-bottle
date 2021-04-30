import os

import pytest
from flask import current_app
from pytest_httpserver import HTTPServer

from ..app import app


@pytest.fixture(scope="function")
def client(httpserver: HTTPServer):
    app.config["PUBLIC_URL"] = httpserver.url_for("")
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_calling_restults_with_get_method_returns_405(client):
    rv = client.get("/test")
    assert rv.status_code == 405


def test_calling_restults_with_post_method_returns_200(client):
    rv = client.post("/test", data={})
    assert rv.status_code == 200


def test_default_path_is_in_temp_dir():
    with app.app_context():
        assert app.config["DATA_DIR"].startswith("/tmp")
