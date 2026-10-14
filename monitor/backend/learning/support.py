import json
from datetime import timedelta
from pathlib import Path

from monitor.backend.db import connect_db
from .normalize import received_time

DATA_PATH = Path(__file__).with_name('data') / 'observation.json'


def read_observation():
    with DATA_PATH.open(encoding='utf-8-sig') as handle:
        rows = json.load(handle)
    if not isinstance(rows, list):
        raise ValueError('observation.json은 원본 행 목록이어야 합니다.')
    return rows


def current_boundary():
    with connect_db() as conn:
        return conn.execute('SELECT COALESCE(MAX(id), 0) AS after_id FROM http_events').fetchone()['after_id']


def read_recent(after_id, reference_time=None):
    with connect_db() as conn:
        reference = (received_time(reference_time) if reference_time is not None
                     else conn.execute('SELECT clock_timestamp() AS reference').fetchone()['reference'])
        rows = conn.execute(
            'SELECT id, occurred_at, method, path, status_code, event_type FROM http_events '
            'WHERE id > %s AND occurred_at >= %s AND occurred_at <= %s ORDER BY id',
            (after_id, reference - timedelta(seconds=60), reference)).fetchall()
    return rows, reference.isoformat()
