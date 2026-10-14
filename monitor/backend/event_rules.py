"""Validate and classify server request records without inventing identities."""

EVENT_TYPES = {'http_request', 'login_success', 'login_failure', 'post_list', 'request_error'}


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
    event_type = 'request_error' if status >= 400 else 'http_request'
    if method == 'GET' and path == '/' and status == 200:
        event_type = 'post_list'
    if method == 'POST' and path == '/auth/login':
        event_type = {200: 'login_success', 401: 'login_failure'}.get(status, event_type)
    return dict(method=method, path=path, status_code=status, event_type=event_type)
