import json
import logging
import os
import tempfile
from datetime import datetime
from os import environ, makedirs
from shutil import make_archive

from flask import (
    Flask,
    abort,
    jsonify,
    make_response,
    render_template,
    request,
    send_file,
)

from .decorators import requires_authentication_token


def create_app(testing=False):
    # create and configure the app
    app = Flask(__name__)

    if testing:
        app.config["DATA_DIR"] = "./tests/__data"
        makedirs(app.config["DATA_DIR"], exist_ok=True)
    elif "DATA_DIR" in environ:
        app.config["DATA_DIR"] = environ["DATA_DIR"]
    else:
        app.config["DATA_DIR"] = tempfile.mkdtemp()

    app.config["AUTH_TOKEN"] = environ["AUTH_TOKEN"]

    app.logger.setLevel(logging.INFO)

    @app.route("/<survey>", methods=["GET"])
    def survey(survey):
        """Displays survey"""
        try:
            with open(
                os.path.join(app.config["DATA_DIR"], survey, "survey.json")
            ) as survey:
                survey_spec = json.load(survey)
                return render_template(
                    "survey.html",
                    survey_spec=survey_spec,
                    survey_title=survey_spec["pages"][0]["title"],
                )
        except FileNotFoundError:
            abort(404)
        except json.JSONDecodeError as e:
            app.logger.error(f"Received invalid data for survey name {survey}")
            abort(505)

    @app.route("/<survey>", methods=["POST"])
    def results(survey):
        """Handles results form surveys"""
        try:
            json_response = json.loads(request.data)
            with open(
                tempfile.mkstemp(
                    dir=os.path.join(app.config["DATA_DIR"], survey, "results"),
                    prefix=str(int(datetime.now().timestamp())),
                    suffix=".json",
                )[1],
                "w",
            ) as result_file:
                result_file.write(json.dumps(json_response, indent=2, sort_keys=True))
                result_file.close()
        except FileNotFoundError:
            app.logger.error(f"Received data for invalid survey name {survey}")
        except json.JSONDecodeError as e:
            app.logger.error(f"Received invalid data for survey name {survey}")
        return jsonify({})

    @app.route("/<survey>", methods=["PUT"])
    @requires_authentication_token
    def create_survey(survey):
        """Displays survey"""
        try:
            makedirs(os.path.join(app.config["DATA_DIR"], survey), exist_ok=True)
            json_response = json.loads(request.data)
            with open(
                os.path.join(app.config["DATA_DIR"], survey, "survey.json"), "w"
            ) as survey_file:
                json.dump(json_response, survey_file, indent=2, sort_keys=True)
        except json.JSONDecodeError as e:
            app.logger.error(f"Received invalid data for new survey {survey}")
            abort(500)
        return jsonify({})

    @app.route("/<survey>/results", methods=["GET"])
    @requires_authentication_token
    def export_results(survey):
        export_path = os.path.join(app.config["DATA_DIR"], "export")
        makedirs(export_path, exist_ok=True)
        result_files = os.listdir(
            os.path.join(app.config["DATA_DIR"], survey, "results")
        )
        if len(result_files) == 0:
            return make_response(jsonify({}), 204)
        else:
            make_archive(
                os.path.join(export_path, survey),
                "gztar",
                os.path.join(app.config["DATA_DIR"], survey),
            )
            response = make_response(
                send_file(os.path.join(export_path, f"{survey}.tar.gz"))
            )
            response.headers.set("Content-Type", "application/x-tgz")
            return response

    return app


if __name__ == "__main__":
    create_app().run()
