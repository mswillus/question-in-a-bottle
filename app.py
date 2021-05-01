import json
import logging
import tempfile
from datetime import datetime
from os import environ, makedirs

from flask import Flask, jsonify, request


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

    app.logger.setLevel(logging.INFO)

    @app.route("/<survey>", methods=["POST"])
    def results(survey):
        """Handles results form surveys"""
        result_file = tempfile.mkstemp(
            dir=app.config["DATA_DIR"],
            prefix=str(int(datetime.now().timestamp())),
            suffix=".json",
        )
        try:
            json_response = json.loads(request.data)
            result_file.write(json.dumps(json_response, indent=2, sort_keys=True))
        except json.JSONDecodeError as e:
            app.logger.error(e.msg)
        return jsonify({})

    return app


if __name__ == "__main__":
    create_app().run()
