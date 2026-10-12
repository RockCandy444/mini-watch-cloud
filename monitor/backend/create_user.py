import getpass
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from werkzeug.security import generate_password_hash
from monitor.backend.repositories.users import create_user

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--classroom', action='store_true', help='실습 전용 operator 계정 준비')
    args = parser.parse_args()
    username = 'operator' if args.classroom else input('운영자 아이디: ').strip()
    password = 'Learn123!' if args.classroom else getpass.getpass('비밀번호: ')
    confirm = password if args.classroom else getpass.getpass('비밀번호 확인: ')
    if not username or not password.strip() or password != confirm:
        raise SystemExit('입력값 또는 비밀번호 확인이 올바르지 않습니다.')
    result = create_user(username, generate_password_hash(password))
    print('계정을 만들었습니다.' if result else '이미 있는 아이디입니다. 기존 계정은 유지합니다.')
