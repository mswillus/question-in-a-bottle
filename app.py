import json
import logging
import tempfile
from os import environ

from flask import Flask, jsonify, request

app = Flask(__name__)

if "DATA_DIR" in environ:
    app.config["DATA_DIR"] = environ["DATA_DIR"]
else:
    app.config["DATA_DIR"] = tempfile.mkdtemp()

app.logger.setLevel(logging.INFO)


@app.route("/<survey>", methods=["POST"])
def results(survey):
    """Handles results form surveys"""
    result_file = tempfile.mkstemp(dir=app.config["DATA_DIR"])
    try:
        json_response = json.loads(request.data)
        result_file.write(json.dumps(json_response, indent=2, sort_keys=True))
    except json.JSONDecodeError as e:
        app.logger.error(e.msg)
    return jsonify({})


if __name__ == "__main__":
    app.run()
