from functools import wraps

from flask import abort, current_app, request


def requires_authentication_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if (
            "authorization" not in request.headers
            or request.headers["authorization"]
            != f"Token {current_app.config['AUTH_TOKEN']}"
        ):
            abort(403)
        return f(*args, **kwargs)

    return decorated_function
