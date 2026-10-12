from getpass import getpass

import requests


if __name__ == "__main__":
    username = input("아이디 [student]: ").strip() or "student"
    password = getpass("비밀번호: ")
    response = requests.post(
        "http://127.0.0.1:5100/auth/login",
        json={"username": username, "password": password},
        timeout=5,
    )
    print(response.status_code)
    print(response.json())
