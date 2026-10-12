"""Disposable PostgreSQL schema for browser verification. Never edits existing notes.
Run from mini-watch with the existing backend Python environment.
Press Ctrl+C to stop and drop only this uniquely named test schema.
"""
import uuid
from pathlib import Path
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server
from monitor.backend.app import create_app
from monitor.backend.db import connect_db, orm_engine
from monitor.backend.repositories import notes, events, users

schema = 'task50_e2e_' + uuid.uuid4().hex

def test_connection():
    conn = connect_db()
    conn.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
    return conn

if __name__ == '__main__':
    with connect_db() as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    engine = None
    try:
        with test_connection() as conn:
            conn.execute(Path('monitor/backend/sql/prepare_monitor.sql').read_text(encoding='utf-8'))
            conn.execute('INSERT INTO monitor_users (username, password_hash) VALUES (%s, %s)', ('task50_tester', generate_password_hash('task50-test-only-password')))
        notes.connect_db = test_connection
        events.connect_db = test_connection
        engine = create_engine(orm_engine.url, connect_args={'options': '-csearch_path=' + schema})
        users.session_scope = sessionmaker(engine).begin
        app = create_app({'SECRET_KEY': 'task50-disposable-test-session', 'FRONTEND_ORIGIN': 'http://127.0.0.1:5173'})
        server = make_server('127.0.0.1', 5201, app, threaded=True)
        print('Disposable PostgreSQL browser verification API ready: http://127.0.0.1:5201', flush=True)
        print('User: task50_tester (test-only fixture); existing user data is preserved.', flush=True)
        server.serve_forever()
    finally:
        if engine:
            engine.dispose()
        with connect_db() as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
        print('Disposable verification schema removed.', flush=True)
