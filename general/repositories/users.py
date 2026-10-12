from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from db import session_scope
from models import User


def find_user(username):
    with session_scope() as session:
        user = session.scalar(select(User).where(User.username == username))
        return None if user is None else {
            "id": user.id, "username": user.username, "password_hash": user.password_hash,
        }


def create_user(username, password_hash):
    try:
        with session_scope() as session:
            user = User(username=username, password_hash=password_hash)
            session.add(user)
            session.flush()
            result = {"id": user.id, "username": user.username}
        return result
    except IntegrityError as error:
        # The unique constraint also handles simultaneous registrations.
        if getattr(error.orig, "sqlstate", None) == "23505":
            return None
        raise
