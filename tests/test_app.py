import os
from datetime import datetime

import pytest
from flask import current_app
from pytest_httpserver import HTTPServer

from ..app import create_app


@pytest.fixture(scope="function")
def client(httpserver: HTTPServer):
    app = create_app(testing=True)
    app.config["PUBLIC_URL"] = httpserver.url_for("")
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def flush_data_dir():
    data_dir = create_app(testing=True).config["DATA_DIR"]
    for filename in os.listdir(data_dir):
        os.remove(os.path.join(data_dir, filename))


def test_calling_restults_with_get_method_returns_405(client):
    rv = client.get("/test")
    assert rv.status_code == 405


def test_calling_restults_with_post_method_returns_200(client):
    rv = client.post("/test", data={})
    assert rv.status_code == 200


def test_default_path_is_in_temp_dir():
    app = create_app()
    with app.app_context():
        assert app.config["DATA_DIR"].startswith("/tmp")


def test_path_override():
    os.environ["DATA_DIR"] = "./"
    app = create_app()
    with app.app_context():
        assert app.config["DATA_DIR"].startswith("./")


def test_writes_file(client):
    flush_data_dir()
    rv = client.post("/test", data={})
    assert len(os.listdir(client.application.config["DATA_DIR"])) == 1


def test_post_writes_file_with_timestamp_prefix_writes_file(client, freezer):
    now = datetime.now()
    flush_data_dir()
    rv = client.post("/test", data={})
    filename = os.listdir(client.application.config["DATA_DIR"])[0]
    assert str(int(now.timestamp())) in filename
