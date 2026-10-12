from flask import Blueprint, request
from monitor.backend.repositories import events
from monitor.backend.routes.auth import require_login

events_bp = Blueprint('monitor_events', __name__, url_prefix='/api/events')
EVENT_TYPES = {'http_request', 'login_success', 'login_failure'}


def make_event(data):
    if not isinstance(data, dict):
        return None
    method, path, status = data.get('method'), data.get('path'), data.get('status_code')
    if not isinstance(method, str) or method not in {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'}:
        return None
    if not isinstance(path, str) or not path.startswith('/') or len(path) > 500:
        return None
    if type(status) is not int or not 100 <= status <= 599:
        return None
    event_type = 'http_request'
    if method == 'POST' and path == '/auth/login':
        event_type = {200: 'login_success', 401: 'login_failure'}.get(status, event_type)
    return dict(method=method, path=path, status_code=status, event_type=event_type)


@events_bp.post('')
def receive():
    # General service ingestion stays open on loopback. Reads require login.
    event = make_event(request.get_json(silent=True))
    if event is None:
        return {'error': 'method, path, status_code를 올바르게 보내 주세요.'}, 400
    return {'message': '기록을 받았습니다.', **events.create_event(event)}, 201


@events_bp.get('')
@require_login
def index():
    status = request.args.get('status') or None
    event_type = request.args.get('event_type') or None
    if event_type is not None and event_type not in EVENT_TYPES:
        return {'error': '지원하지 않는 이벤트 종류입니다.'}, 400
    if status is not None and status != 'errors':
        if not status.isdecimal() or not 100 <= int(status) <= 599:
            return {'error': '상태 코드는 100~599 또는 errors여야 합니다.'}, 400
        status = int(status)
    rows = events.list_events(request.args.get('path', '').strip(), status, event_type)
    return {'events': rows, 'summary': {'total': len(rows), 'errors': sum(row['status_code'] >= 400 for row in rows)}}
