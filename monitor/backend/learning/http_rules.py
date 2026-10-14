from .normalize import received_time


def select_views(rows):
    return [row for row in rows if row.get('method') == 'GET'
            and row.get('path') == '/' and row.get('status_code') == 200
            and row.get('kind') == 'post_list']


def find_following_errors(rows, views, seconds=30):
    if not views:
        return []
    last = max(received_time(row['occurred_at']) for row in views)
    return [row for row in rows if row.get('status_code') == 404
            and 0 < (received_time(row['occurred_at']) - last).total_seconds() <= seconds]


def analyze_http(rows, threshold=10):
    if type(threshold) is not int or not 1 <= threshold <= 100000:
        raise ValueError('기준은 1~100000의 정수여야 합니다.')
    views = select_views(rows)
    errors = find_following_errors(rows, views)
    records = sorted(views + errors, key=lambda row: (received_time(row['occurred_at']), int(row['id'][5:])))
    return {'count': len(views), 'threshold': threshold, 'matched': len(views) >= threshold,
            'view_ids': [row['id'] for row in views],
            'following_error_ids': [row['id'] for row in errors],
            'records': records, 'evidence': [row['id'] for row in records]}
