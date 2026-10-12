from flask import Blueprint, render_template, request
from werkzeug.security import check_password_hash, generate_password_hash

from repositories.users import find_user, create_user
from common.registration import allowed_origin, validate_registration

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/auth/register")
def register():
    if not allowed_origin():
        return {"error": "허용되지 않은 요청 출처입니다."}, 403
    try:
        username, password = validate_registration(request.get_json(silent=True))
    except ValueError as error:
        return {"error": str(error)}, 400
    user = create_user(username, generate_password_hash(password, method="scrypt"))
    if user is None:
        return {"error": "이미 사용 중인 아이디입니다."}, 409
    return {"message": "회원가입이 완료되었습니다. 로그인해 주세요.", "user": user}, 201


@auth_bp.get("/login")
def login_page():
    return render_template("login.html")


@auth_bp.post("/auth/login")
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {"error": "아이디와 비밀번호를 JSON으로 보내 주세요."}, 400
    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return {"error": "아이디와 비밀번호를 문자열로 보내 주세요."}, 400
    if not username.strip() or not password.strip():
        return {"error": "아이디와 비밀번호를 모두 입력해 주세요."}, 400
    user = find_user(username.strip())
    if user is None or not check_password_hash(user["password_hash"], password):
        return {"error": "아이디 또는 비밀번호가 올바르지 않습니다."}, 401
    return {
        "message": "로그인 성공",
        "user": {"id": user["id"], "username": user["username"]},
    }
