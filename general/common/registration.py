import re

from flask import current_app, request


def validate_registration(data):
    if not isinstance(data, dict):
        raise ValueError("회원가입 정보를 JSON으로 보내 주세요.")
    username = data.get("username")
    password = data.get("password")
    confirm = data.get("password_confirm")
    if not all(isinstance(value, str) for value in (username, password, confirm)):
        raise ValueError("아이디, 비밀번호, 비밀번호 확인을 모두 입력해 주세요.")
    username = username.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,30}", username):
        raise ValueError("아이디는 영문, 숫자, 밑줄, 하이픈으로 3~30자 입력해 주세요.")
    if not 8 <= len(password) <= 128 or not password.strip():
        raise ValueError("비밀번호는 공백만 사용하지 않고 8~128자로 입력해 주세요.")
    if password != confirm:
        raise ValueError("비밀번호 확인이 일치하지 않습니다.")
    return username, password


def allowed_origin():
    origin = request.headers.get("Origin")
    return not origin or origin.rstrip("/") in {
        request.host_url.rstrip("/"),
        current_app.config["FRONTEND_ORIGIN"].rstrip("/"),
    }
