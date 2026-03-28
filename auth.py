from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import current_app, jsonify, request
from jose import JWTError, jwt


def encode_token(customer_id):
    """Create a signed JWT token for a customer."""
    payload = {
        "sub": str(customer_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc),
        "type": "customer",
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def token_required(route_function):
    """Validate Bearer token and pass customer_id to the decorated route."""

    @wraps(route_function)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            if payload.get("type") != "customer":
                return jsonify({"error": "Invalid token type"}), 401
            subject = payload.get("sub")
            if subject is None:
                return jsonify({"error": "Invalid token payload"}), 401
            customer_id = int(subject)
        except (JWTError, ValueError, TypeError):
            return jsonify({"error": "Invalid or expired token"}), 401

        return route_function(customer_id, *args, **kwargs)

    return wrapper
