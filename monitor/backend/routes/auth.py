from functools import wraps
from flask import Blueprint, g, request, session
from werkzeug.security import check_password_hash, generate_password_hash
from common.registration import allowed_origin, validate_registration
from monitor.backend.repositories import users

auth_bp = Blueprint('monitor_auth', __name__, url_prefix='/api/auth')


def require_login(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get('user_id')
        g.user = users.find_user(user_id) if user_id is not None else None
        if g.user is None:
            session.clear()
            return {'error': '로그인이 필요합니다.'}, 401
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            if not allowed_origin():
                return {'error': '허용되지 않은 요청 출처입니다.'}, 403
        return view(*args, **kwargs)
    return wrapped


@auth_bp.post('/register')
def register():
    if not allowed_origin():
        return {'error': '허용되지 않은 요청 출처입니다.'}, 403
    try:
        username, password = validate_registration(request.get_json(silent=True))
    except ValueError as error:
        return {'error': str(error)}, 400
    user = users.create_user(username, generate_password_hash(password, method='scrypt'))
    if user is None:
        return {'error': '이미 사용 중인 아이디입니다.'}, 409
    return {'message': '회원가입이 완료되었습니다. 로그인해 주세요.', 'user': user}, 201


@auth_bp.post('/login')
def login():
    if not allowed_origin():
        return {'error': '허용되지 않은 요청 출처입니다.'}, 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {'error': '아이디와 비밀번호를 입력해 주세요.'}, 400
    username, password = data.get('username'), data.get('password')
    if not isinstance(username, str) or not isinstance(password, str) or not username.strip() or not password.strip():
        return {'error': '아이디와 비밀번호를 입력해 주세요.'}, 400
    session.clear()
    user = users.find_by_username(username.strip())
    if user is None or not check_password_hash(user['password_hash'], password):
        return {'error': '아이디 또는 비밀번호가 맞지 않습니다.'}, 401
    session['user_id'] = user['id']
    return {'user': {'id': user['id'], 'username': user['username']}}


@auth_bp.get('/me')
@require_login
def me():
    return {'user': g.user}


@auth_bp.post('/logout')
@require_login
def logout():
    session.clear()
    return {'message': '로그아웃했습니다.'}
