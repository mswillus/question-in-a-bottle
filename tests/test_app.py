import json
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


def survey_factory(survey):
    data_dir = create_app(testing=True).config["DATA_DIR"]
    os.makedirs(os.path.join(data_dir, survey), exist_ok=True)


def flush_survey_dir(survey):
    data_dir = create_app(testing=True).config["DATA_DIR"]
    try:
        for filename in os.listdir(os.path.join(data_dir, survey)):
            os.remove(os.path.join(data_dir, survey, filename))
        os.rmdir(os.path.join(data_dir, survey))
    except FileNotFoundError:
        pass


def test_calling_restults_with_get_method_returns_405(client):
    rv = client.get("/test")
    assert rv.status_code == 405


def test_calling_restults_with_post_method_returns_200(client):
    survey_factory("test")
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


def test_writes_file_to_subfolder(client):
    flush_survey_dir("test")
    survey_factory("test")
    rv = client.post("/test", json={})
    assert (
        len(os.listdir(os.path.join(client.application.config["DATA_DIR"], "test")))
        == 1
    )


def test_posting_to_non_extisting_survey_logs_error(client, caplog):
    rv = client.post("/malformed", json={})
    for record in caplog.records:
        assert "invalid survey" in str(record)


def test_post_writes_file_with_timestamp_prefix_writes_file(client, freezer):
    now = datetime.now()
    flush_survey_dir("test")
    survey_factory("test")
    rv = client.post("/test", json={})
    filename = os.listdir(os.path.join(client.application.config["DATA_DIR"], "test"))[
        0
    ]
    assert str(int(now.timestamp())) in filename


def test_post_writes_file_with_timestamp_prefix_writes_file(client):
    flush_survey_dir("test")
    survey_factory("test")
    data = {"1234": 5678}
    rv = client.post("/test", json=data)
    filename = os.listdir(os.path.join(client.application.config["DATA_DIR"], "test"))[
        0
    ]
    with open(
        os.path.join(client.application.config["DATA_DIR"], "test", filename)
    ) as survey_file:
        assert data == json.load(survey_file)
