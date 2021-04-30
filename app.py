import logging

from flask import Flask, abort

app = Flask(__name__)

app.logger.setLevel(logging.INFO)

@app.route("/", methods=["GET", "POST"])
def results():
    """Handles results form surveys
    """
    return abort(404)

if __name__ == "__main__":
    app.run()
