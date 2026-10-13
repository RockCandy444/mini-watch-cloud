import hmac
import secrets
from flask import session


def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def valid_csrf(token):
    expected = session.get("csrf_token")
    return isinstance(token, str) and isinstance(expected, str) and hmac.compare_digest(token.encode(), expected.encode())
