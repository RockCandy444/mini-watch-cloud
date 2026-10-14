from datetime import datetime, timezone
from flask import Blueprint, request
from monitor.backend.routes.auth import require_login
from monitor.backend.learning.normalize import received_time
from monitor.backend.learning.support import current_boundary, read_recent
from monitor.backend.learning.report import build_report

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')


def integer_arg(name, minimum, maximum, default=None):
    values = request.args.getlist(name)
    value = values[0] if len(values) == 1 else (default if not values else None)
    if value is None or not value.isascii() or not value.isdecimal() or len(value) > 19:
        raise ValueError(f'{name}: 정수가 필요합니다.')
    number = int(value)
    if not minimum <= number <= maximum:
        raise ValueError(f'{name}: {minimum}~{maximum} 범위여야 합니다.')
    return number


@analysis_bp.get('/observation')
@require_login
def observation():
    # Read a new boundary; never delete history or start a timer.
    return {'after_id': current_boundary(), 'window_seconds': 60}


@analysis_bp.get('')
@require_login
def analysis():
    try:
        threshold = integer_arg('threshold', 1, 100000, '10')
        after_id = integer_arg('after_id', 0, 2147483647)
        reference_values = request.args.getlist('reference_time')
        if len(reference_values) > 1:
            raise ValueError('reference_time은 한 번만 입력합니다.')
        reference = reference_values[0] if reference_values else None
        if reference is not None:
            if len(reference) > 40:
                raise ValueError('reference_time 형식이 올바르지 않습니다.')
            reference = received_time(reference)
            if reference > datetime.now(timezone.utc):
                raise ValueError('미래 기준시각은 사용할 수 없습니다.')
    except (ValueError, TypeError, OverflowError):
        return {'error': '기준은 1~100000, 시작 ID는 0 이상의 정수, 기준시각은 시간대를 포함한 미래가 아닌 ISO 시각이어야 합니다.'}, 400
    rows, reference = read_recent(after_id, reference)
    return build_report(rows, threshold, after_id, reference)
