import hmac
from flask import Blueprint, request, current_app
from monitor.backend.repositories import events
from monitor.backend.routes.auth import require_login
from monitor.backend.event_rules import EVENT_TYPES, make_event

events_bp = Blueprint('monitor_events', __name__, url_prefix='/api/events')


@events_bp.post('')
def receive():
    expected = current_app.config['EVENT_TOKEN']
    token = request.headers.get('X-Event-Token', '')
    if not expected or not hmac.compare_digest(token.encode(), expected.encode()):
        return {'error': '기록 전송 토큰이 올바르지 않습니다.'}, 403
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
