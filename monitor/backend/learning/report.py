from .http_rules import analyze_http
from .normalize import normalize_events


def build_report(originals, threshold=10, after_id=0, reference_time=None):
    result = analyze_http(normalize_events(originals), threshold)
    count, error_count = result['count'], len(result['following_error_ids'])
    card = {'id': 'http-list-frequency', 'title': 'HTTP 목록 조회',
            'observed': count, 'threshold': threshold, 'matched': result['matched'],
            'verdict': '검토 후보' if result['matched'] else '기준 미해당',
            'reason': f'목록 조회 {count}회 >= 기준 {threshold}: {result["matched"]}. '
                      f'마지막 조회 뒤 30초 이내의 404 {error_count}행은 문맥 근거이며 조회 횟수에 더하지 않습니다.',
            'evidence': result['evidence'], 'records': result['records'],
            'view_ids': result['view_ids'], 'following_error_ids': result['following_error_ids']}
    return {'after_id': after_id, 'reference_time': reference_time,
            'window_seconds': 60, 'cards': [card],
            'limitation': '같은 서비스의 시간상 문맥입니다. 사용자·IP·인과관계·침해 또는 정상 여부를 확정하지 않습니다.'}
