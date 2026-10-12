from monitor.backend.db import connect_db


def create_event(event):
    with connect_db() as conn:
        return conn.execute('INSERT INTO http_events (method, path, status_code, event_type) VALUES (%s, %s, %s, %s) RETURNING id', (event['method'], event['path'], event['status_code'], event['event_type'])).fetchone()


def list_events(path='', status=None, event_type=None):
    clauses, params = [], []
    if path:
        clauses.append('strpos(lower(path), lower(%s)) > 0')
        params.append(path)
    if status == 'errors':
        clauses.append('status_code >= 400')
    elif status is not None:
        clauses.append('status_code = %s')
        params.append(status)
    if event_type:
        clauses.append('event_type = %s')
        params.append(event_type)
    where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
    with connect_db() as conn:
        return conn.execute('SELECT * FROM http_events' + where + ' ORDER BY id DESC', params).fetchall()
