# 모아 게시판 실행과 제출

Flask, Jinja2, PostgreSQL을 사용하는 수업용 CRUD 게시판입니다.
기존 `.env`, `db.py`, 로그인 판정 API, 연습 파일, `monitor/backend`는 유지합니다.

## 실행

기존 가상환경을 사용합니다. 아래는 PowerShell 명령입니다.

첫 번째 터미널에서 감시 서비스를 실행합니다.

```powershell
cd C:\work\mini-watch\monitor\backend
.\venv\Scripts\python.exe app.py
```

두 번째 터미널에서 일반 서비스를 실행합니다.

```powershell
cd C:\work\mini-watch\general
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe prepare_db.py
.\venv\Scripts\python.exe app.py
```

가상환경이 활성화되어 있으면 `python app.py`로도 실행할 수 있습니다.
서버가 이미 실행 중이면 해당 터미널에서 Ctrl+C를 누른 후 다시 실행합니다.

- 게시판: http://127.0.0.1:5100/
- 로그인 판정 화면: http://127.0.0.1:5100/login
- 수집된 요청 기록: http://127.0.0.1:5200/api/events
- 기존 JSON 조회: http://127.0.0.1:5100/posts/1

`prepare_db.py`는 `sql/prepare_posts.sql`을 실행합니다. 기존 posts가 없으면 만들고,
자동 번호 설정이 없는 기존 테이블에는 시퀀스를 연결합니다. 기존 행은 삭제하지 않으며,
시퀀스 연결 후에는 기존 최대 번호 다음부터 새 글 번호를 생성합니다.
이미 설정된 자동 번호는 유지하므로 준비 스크립트를 반복 실행할 수 있습니다.

## 파일 역할

| 파일 | 역할 |
| --- | --- |
| `general/app.py` | 앱 생성·설정·Blueprint·요청 기록 등록·실행 |
| `general/db.py` | 기존 PostgreSQL 공통 연결 함수 |
| `general/post_rules.py` | 작성·수정 공통 입력 검사 |
| `general/repositories/posts.py` | 목록·개별 조회·작성·수정·삭제 SQL |
| `general/repositories/users.py` | 기존 사용자 조회 SQL |
| `general/routes/posts.py` | 게시판 HTTP 처리 및 기존 JSON 조회 |
| `general/routes/auth.py` | 기존 로그인 판정 및 로그인 화면 |
| `general/request_logging.py` | 요청 기록을 기존 감시 서비스에 JSON 전송 |
| `general/templates/` | Jinja2 화면 |
| `general/static/` | CSS와 로그인 fetch JavaScript |
| `general/sql/prepare_posts.sql` | 게시글 테이블·시퀀스 준비 |
| `general/tests/test_posts.py` | 실제 PostgreSQL 및 감시 HTTP 통합 검증 |

폼 오류는 HTTP 400, 없는 글은 404, 저장·수정·삭제 후 이동은 303입니다.
삭제 확인의 GET은 조회만 수행하고 실제 삭제는 POST로 처리합니다.
로그인은 수업의 성공·실패 판정 기능이며 세션이나 접근 제한을 추가하지 않습니다.

## 통합 검증

```powershell
cd C:\work\mini-watch\general
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

테스트는 `.env`로 연결한 PostgreSQL에 고유한 `crud_test_*` 스키마를 생성하고,
테스트를 마친 뒤 해당 스키마를 제거합니다. 기존 posts/users 데이터는 변경하지 않습니다.
실제 감시 서비스 코드를 임시 포트에서 실행해 `requests` JSON 전송을 검증합니다.
DB 사용자는 테스트용 스키마 생성 권한이 있어야 합니다.

직접 확인하려면 목록에서 새 글 작성 → 상세 → 수정 → 상세 → 삭제 확인 → 취소 →
상세 → 삭제 확인 → 삭제 → 목록 순서로 진행하세요. 공백뿐인 제목·내용의 오류도 확인하세요.

## 제출

과제 페이지에서 ZIP 파일 또는 GitHub 저장소를 선택할 수 있습니다.
`.env`, 가상환경, Python 캐시, 비밀번호는 제출 파일이나 Git에 포함하지 마세요.
GitHub 제출은 구현 커밋을 저장소에 올린 뒤 저장소 주소를 입력합니다.
ZIP 제출도 코드의 역할 구분을 유지하도록 `general`과 `monitor/backend`를 함께 포함하세요.
