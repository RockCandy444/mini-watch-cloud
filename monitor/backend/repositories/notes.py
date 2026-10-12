from monitor.backend.db import connect_db


def list_notes():
    with connect_db() as conn:
        return conn.execute('SELECT id, title, status, updated_at FROM notes ORDER BY id DESC').fetchall()


def find_note(note_id):
    with connect_db() as conn:
        return conn.execute('SELECT * FROM notes WHERE id = %s', (note_id,)).fetchone()


def create_note(title, body, status):
    with connect_db() as conn:
        return conn.execute('INSERT INTO notes (title, body, status) VALUES (%s, %s, %s) RETURNING *', (title, body, status)).fetchone()


def update_note(note_id, title, body, status):
    with connect_db() as conn:
        return conn.execute('UPDATE notes SET title = %s, body = %s, status = %s, updated_at = NOW() WHERE id = %s RETURNING *', (title, body, status, note_id)).fetchone()


def delete_note(note_id):
    with connect_db() as conn:
        return conn.execute('DELETE FROM notes WHERE id = %s RETURNING id', (note_id,)).fetchone()
