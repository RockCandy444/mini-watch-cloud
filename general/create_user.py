from getpass import getpass
import argparse

from werkzeug.security import generate_password_hash

from repositories.users import create_user


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--classroom", action="store_true", help="실습 전용 student 계정 준비")
    args = parser.parse_args()
    username = "student" if args.classroom else (input("만들 사용자 이름 [student]: ").strip() or "student")
    password = "Learn123!" if args.classroom else getpass("비밀번호: ")
    if not password.strip():
        raise SystemExit("비밀번호를 입력해 주세요.")
    result = create_user(username, generate_password_hash(password))
    print(f"{username} 계정을 만들었습니다." if result else f"{username} 계정이 이미 있습니다. 기존 계정을 유지합니다.")
