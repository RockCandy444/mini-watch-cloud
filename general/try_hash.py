from getpass import getpass

from werkzeug.security import check_password_hash, generate_password_hash


if __name__ == "__main__":
    password = getpass("해시를 만들 비밀번호: ")
    password_hash = generate_password_hash(password)
    print("비밀번호 해시:", password_hash)
    print("일치 여부:", check_password_hash(password_hash, password))
