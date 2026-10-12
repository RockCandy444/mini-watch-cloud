from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from monitor.backend.db import session_scope
from monitor.backend.models import MonitorUser


def find_by_username(username):
    with session_scope() as session:
        user = session.scalar(select(MonitorUser).where(MonitorUser.username == username))
        return None if user is None else {
            'id': user.id, 'username': user.username, 'password_hash': user.password_hash,
        }


def find_user(user_id):
    with session_scope() as session:
        user = session.get(MonitorUser, user_id)
        return None if user is None else {'id': user.id, 'username': user.username}


def create_user(username, password_hash):
    try:
        with session_scope() as session:
            user = MonitorUser(username=username, password_hash=password_hash)
            session.add(user)
            session.flush()
            result = {'id': user.id, 'username': user.username}
        return result
    except IntegrityError as error:
        if getattr(error.orig, 'sqlstate', None) == '23505':
            return None
        raise
