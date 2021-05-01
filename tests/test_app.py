import json
import os
import shutil
import tempfile
from datetime import datetime

import pytest
from bs4 import BeautifulSoup
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
    survey_spec = {
        "pages": [
            {
                "name": "page1",
                "elements": [
                    {
                        "type": "rating",
                        "name": "question1",
                        "title": "What do you think about this test?",
                        "isRequired": True,
                        "rateValues": [
                            {"value": 1, "text": "Awesome!"},
                            {"value": 2, "text": "Pretty lame"},
                        ],
                    }
                ],
                "title": "Test survey",
                "description": "A minimal survey used for testing purposes",
            }
        ]
    }
    os.makedirs(os.path.join(data_dir, survey), exist_ok=True)
    os.makedirs(os.path.join(data_dir, survey, "results"), exist_ok=True)
    with open(os.path.join(data_dir, survey, "survey.json"), "w") as survey_spec_file:
        json.dump(survey_spec, survey_spec_file, indent=2)


def result_factory(survey):
    data_dir = create_app(testing=True).config["DATA_DIR"]
    with open(
        os.path.join(
            data_dir,
            survey,
            "results",
            f"{str(int(datetime.now().timestamp()))}-xyz.json",
        ),
        "w",
    ) as result_file:
        json.dump({"question1": 1}, result_file, indent=2)


def flush_survey_dir(survey):
    data_dir = create_app(testing=True).config["DATA_DIR"]
    try:
        for filename in os.listdir(os.path.join(data_dir, survey, "results")):
            os.remove(os.path.join(data_dir, survey, "results", filename))
        os.rmdir(os.path.join(data_dir, survey, "results"))
        for filename in os.listdir(os.path.join(data_dir, survey)):
            os.remove(os.path.join(data_dir, survey, filename))
        os.rmdir(os.path.join(data_dir, survey))
    except FileNotFoundError:
        pass


def test_calling_restults_with_get_method_returns_404_if_form_does_not_exist(client):
    flush_survey_dir("test")
    rv = client.get("/test")
    # I expect that the website returns OK and is parsable via html
    assert rv.status_code == 404


def test_calling_restults_with_get_method_returns_html_with_data_when_survey_exists(
    client,
):
    survey_factory("questions")
    rv = client.get("/questions")
    # I expect that the website returns OK and is parsable via html and I a survey container to be presnt
    assert rv.status_code == 200
    page = BeautifulSoup(rv.data, "html.parser")
    assert page.find(id="surveyContainer")


def test_calling_restults_with_post_method_returns_200(client):
    survey_factory("test")
    rv = client.post("/test", data={})
    assert rv.status_code == 200


def test_default_path_is_in_temp_dir():
    del os.environ["DATA_DIR"]
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
        len(
            os.listdir(
                os.path.join(client.application.config["DATA_DIR"], "test", "results")
            )
        )
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
    filename = os.listdir(
        os.path.join(client.application.config["DATA_DIR"], "test", "results")
    )[0]
    assert str(int(now.timestamp())) in filename


def test_post_writes_file_with_timestamp_prefix_writes_file(client):
    flush_survey_dir("test")
    survey_factory("test")
    data = {"1234": 5678}
    rv = client.post("/test", json=data)
    filename = os.listdir(
        os.path.join(client.application.config["DATA_DIR"], "test", "results")
    )[0]
    with open(
        os.path.join(client.application.config["DATA_DIR"], "test", "results", filename)
    ) as survey_file:
        assert data == json.load(survey_file)


def test_post_invalid_data_results_in_error(client, caplog):
    flush_survey_dir("test")
    survey_factory("test")
    rv = client.post("/test", data="Mal Formed")
    for record in caplog.records:
        assert "invalid data" in str(record)


def test_calling_the_put_message_without_auth_token_produces_not_authorized(client):
    rv = client.put("/new", json={"test": 1234})
    assert rv.status_code == 403


def test_calling_the_put_message_with_token_returns_ok(client):
    rv = client.put(
        "/new",
        json={"test": 1234},
        headers={"Authorization": f"Token {client.application.config['AUTH_TOKEN']}"},
    )
    assert rv.status_code == 200


def test_create_new_survey(client):
    # Given there are is no 'test-survey' survey
    flush_survey_dir("test-survey")
    # When I create a new servey called "test-survey"
    rv = client.put(
        "/test-survey",
        json={"test": "wheeee"},
        headers={"Authorization": f"Token {client.application.config['AUTH_TOKEN']}"},
    )
    # I expect that the survey folder was created
    filenames = os.listdir(
        os.path.join(client.application.config["DATA_DIR"], "test-survey")
    )
    assert "survey.json" in filenames
    # And I expect that the file contains the scheme
    with open(
        os.path.join(
            client.application.config["DATA_DIR"], "test-survey", "survey.json"
        )
    ) as survey_file:
        assert {"test": "wheeee"} == json.load(survey_file)


def test_replace_survey(client):
    # Given there are already is a 'test-survey' survey
    flush_survey_dir("test-survey")
    survey_factory("test-survey")
    # When I overwrite the servey called "test-survey"
    rv = client.put(
        "/test-survey",
        json={"test": "whoooo"},
        headers={"Authorization": f"Token {client.application.config['AUTH_TOKEN']}"},
    )
    # I expect that the file contains the new scheme
    with open(
        os.path.join(
            client.application.config["DATA_DIR"], "test-survey", "survey.json"
        )
    ) as survey_file:
        assert {"test": "whoooo"} == json.load(survey_file)


def test_calling_the_restults_endpoint_without_auth_token_produces_not_authorized(
    client,
):
    rv = client.get("/new/results")
    assert rv.status_code == 403


def test_calling_the_results_endpoint_with_auth_token_is_OK(client):
    flush_survey_dir("new")
    survey_factory("new")
    result_factory("new")
    rv = client.get(
        "/new/results",
        headers={"Authorization": f"Token {client.application.config['AUTH_TOKEN']}"},
    )
    assert rv.status_code == 200


def test_calling_the_results_endpoint_for_an_empty_survey_returns_204(client):
    flush_survey_dir("new")
    survey_factory("new")
    rv = client.get(
        "/new/results",
        headers={"Authorization": f"Token {client.application.config['AUTH_TOKEN']}"},
    )
    assert rv.status_code == 204


def test_calling_the_results_endpoint_with_auth_token_creates_and_exports_an_archive_with_results(
    client,
):
    flush_survey_dir("new")
    survey_factory("new")
    result_factory("new")
    rv = client.get(
        "/new/results",
        headers={"Authorization": f"Token {client.application.config['AUTH_TOKEN']}"},
    )
    filenames = os.listdir(
        os.path.join(client.application.config["DATA_DIR"], "export")
    )
    assert "new.tar.gz" in filenames
    tempdir = tempfile.mkdtemp()
    shutil.unpack_archive(
        os.path.join(client.application.config["DATA_DIR"], "export", "new.tar.gz"),
        tempdir,
    )
    assert "survey.json" in os.listdir(tempdir)
    assert "results" in os.listdir(tempdir)
    assert "question1" in json.load(
        open(
            os.path.join(
                tempdir, "results", os.listdir(os.path.join(tempdir, "results"))[0]
            )
        )
    )
