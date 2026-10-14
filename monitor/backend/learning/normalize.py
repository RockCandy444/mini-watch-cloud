from datetime import datetime, timezone


def received_time(value):
    result = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError('수신시각에 시간대가 필요합니다.')
    return result.astimezone(timezone.utc)


def normalize_event(original):
    row = dict(original)
    source_id = row['id']
    if type(source_id) is not int or source_id < 1:
        raise ValueError('원본 ID는 양의 정수여야 합니다.')
    row.update(id=f'http-{source_id}', source='http_live', kind=row['event_type'])
    # Serialize the same instant; never replace DB receipt time with local now().
    row['occurred_at'] = received_time(row['occurred_at']).isoformat()
    return row


def normalize_events(rows):
    return [normalize_event(row) for row in rows]
