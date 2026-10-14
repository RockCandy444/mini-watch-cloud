"""Issue real local requests; emit JSON only after verifying their DB records."""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from monitor.backend.db import setting, connect_db
from .support import current_boundary


def capture_case(count):
    if type(count) is not int or not 1 <= count <= 100:
        raise ValueError('요청 수는 1~100입니다.')
    base = setting('GENERAL_API_URL', 'http://general-api:5000').rstrip('/')
    address = urlsplit(base)
    if (address.scheme != 'http' or address.hostname not in {'general-api', 'localhost', '127.0.0.1'}
            or address.username or address.password or address.path or address.query or address.fragment):
        raise ValueError('캡처는 로컬 일반 서비스의 HTTP 주소만 사용합니다.')
    after_id = current_boundary()
    for path, expected in [('/', 200)] * count + [('/training-missing', 404)]:
        try:
            with urllib.request.urlopen(base + path, timeout=20) as response:
                actual = response.status
                response.read()
        except urllib.error.HTTPError as error:
            actual = error.code
            error.close()
        if actual != expected:
            raise RuntimeError(f'{path}: 예상 {expected}, 실제 {actual}. 캡처를 중단합니다.')
        # DB timestamps must put the missing request strictly after the last view.
        time.sleep(0.05)
    deadline = time.monotonic() + 5
    while True:
        with connect_db() as conn:
            rows = conn.execute(
                'SELECT id, occurred_at, method, path, status_code, event_type FROM http_events '
                'WHERE id > %s ORDER BY id', (after_id,)).fetchall()
        if len(rows) >= count + 1 or time.monotonic() >= deadline:
            break
        time.sleep(0.1)
    expected = [('GET', '/', 200, 'post_list')] * count + [('GET', '/training-missing', 404, 'request_error')]
    actual = [(row['method'], row['path'], row['status_code'], row['event_type']) for row in rows]
    if actual != expected:
        raise RuntimeError('DB 행이 이번 요청과 일치하지 않습니다. 전송 실패 또는 다른 요청을 확인하고 새 관찰로 재시도하세요.')
    return [{**row, 'occurred_at': row['occurred_at'].isoformat()} for row in rows]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('count', type=int)
    args = parser.parse_args()
    try:
        print(json.dumps(capture_case(args.count), ensure_ascii=False, indent=2))
    except Exception as error:
        # Do not print exception contents: connection details may contain secrets.
        print(f'캡처 실패 ({type(error).__name__}). general 전송 경고와 monitor 로그를 확인하세요.', file=sys.stderr)
        sys.exit(1)
