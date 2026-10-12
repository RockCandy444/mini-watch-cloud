# 감시 대시보드 구조와 확인 결과

과제: https://classroom.codemit.kr/classes/5/problems/49/submit

## 요청 흐름

1. `general`의 `after_request`가 실제 HTTP 요청의 메서드·경로·응답 상태를 만들고 `POST /api/events`로 전송합니다.
2. 감시 라우터가 입력을 검사한 뒤 저장소에서 PostgreSQL `http_events`에 저장합니다.
3. React는 Next.js의 `/api` 프록시를 통해 Flask에 요청합니다. 브라우저는 DB에 접속하지 않습니다.
4. 로그인 라우터가 `monitor_users`의 비밀번호 해시를 확인하고 서명된 세션 쿠키를 발급합니다.
5. `App.jsx`가 `/api/auth/me`로 사용자 정보를 확인해 로그인 화면 또는 대시보드를 표시합니다.
6. 운영자가 메모를 저장·수정·삭제하면 성공 응답 후 메모 목록을 다시 읽습니다.

## 파일별 역할

| 파일 | 역할 |
| --- | --- |
| `monitor/backend/app.py` | 앱 설정, Blueprint 등록, JSON 오류 처리, 실행 |
| `monitor/backend/db.py` | `.env`를 읽고 기존 psycopg 연결 및 계정 ORM 세션 구성 |
| `monitor/backend/routes/auth.py` | 해시 검증, 세션 생성·확인·제거, API 보호 데코레이터 |
| `monitor/backend/routes/events.py` | 요청 기록 검증·수집·검색·집계 |
| `monitor/backend/routes/notes.py` | 메모 입력 공통 검사, HTTP 상태 결정 |
| `monitor/backend/repositories/` | 사용자 SQLAlchemy ORM, 기록·메모는 바인딩된 SQL 실행 |
| `monitor/backend/sql/prepare_monitor.sql` | 사용자·요청 기록·메모 테이블 준비 |
| `monitor/frontend/src/App.jsx` | 사용자 state, 로그인 확인·전환 |
| `monitor/frontend/src/api/` | 공통 fetch, 로그인·요청 기록·메모 요청 함수 |
| `monitor/frontend/src/components/` | props로 연결한 로그인, 대시보드, 기록, 메모 목록·상세·폼·삭제 확인 |
| `monitor/frontend/src/style.css` | 공통 반응형 스타일, 좁은 화면에서 한 열로 표시 |

## API

| 요청 | 주소 | 성공 | 실패 |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | 201, user | 입력 400, 중복 409, 출처 403, DB 503 |
| POST | `/api/auth/login` | 200, user | 빈 입력 400, 틀린 계정 401 |
| GET | `/api/auth/me` | 200, user | 미로그인 401 |
| POST | `/api/auth/logout` | 200 | 미로그인 401 |
| POST | `/api/events` | 201, id | 잘못된 기록 400 |
| GET | `/api/events` | 200, events와 summary | 미로그인 401, 잘못된 조건 400 |
| GET | `/api/notes` | 200, notes | 미로그인 401 |
| GET | `/api/notes/<id>` | 200, note | 없는 메모 404 |
| POST | `/api/notes` | 201, note | 빈 제목·본문, 잘못된 상태 400 |
| PUT | `/api/notes/<id>` | 200, note | 잘못된 입력 400, 없는 메모 404 |
| DELETE | `/api/notes/<id>` | 200 | 없는 메모 404 |

보호 API는 로그인하지 않으면 내용 조회·작성·수정·삭제를 모두 401로 거절합니다.
일반 서비스가 자동 기록을 보낼 수 있도록 `POST /api/events`만 로그인 검사에서 제외합니다.
두 Flask 서비스는 `127.0.0.1`에서 실행합니다.

메모 JSON 예: `{"title":"없는 게시글 요청 확인","body":"404 응답을 확인했다.","status":"확인 중"}`.
앞뒤 공백은 서버에서 제거하고 어느 한 항목이 비어 있으면 저장하지 않습니다.

## 선택 기능 4개

- 경로의 대소문자를 구분하지 않는 부분 검색과 상태 코드 필터를 함께 적용합니다. `%`도 검색 문자인 그대로 처리합니다. 조건 해제는 모든 기록을 다시 조회합니다.
- 전체 요청 수·오류 요청 수·오류 외 요청 수를 표시합니다. **오류는 400 이상**, 집계 범위는 **현재 조건으로 조회한 전체 DB 기록**이며 목록을 제한하거나 별도 샘플로 집계하지 않습니다. CSS·favicon 요청도 실제 수집된 자료이므로 포함합니다.
- 메모 상태는 `확인 전`, `확인 중`, `완료`이며 제목·내용과 함께 PostgreSQL에 저장합니다.
- HttpOnly·SameSite=Lax 세션 쿠키로 새로고침 후에도 로그인을 유지합니다. `/api/auth/me`가 사용자를 다시 확인합니다. 같은 `SECRET_KEY`를 사용하면 서버 재실행 뒤에도 유효한 세션이 확인됩니다. 로그아웃은 서버 세션과 React 사용자 state를 비웁니다.

## 2026-10-07 검증 결과

- `npm run build` 성공: Next.js 프로덕션 빌드 및 회원가입 페이지 생성.
- 실제 PostgreSQL 감시 API 통합 테스트 8개 통과. 회원가입 ORM 저장·중복·입력·출처·DB 오류, 로그인 400·401·200, 해시 검증, 세션 쿠키, 로그아웃, 비로그인·위조 쿠키 API 차단, 메모 CRUD, 상태 저장, 입력 오류·없는 번호, 필터·집계, SQL 입력값 바인딩, 준비 SQL 반복 실행 확인.
- 일반 게시판 통합 테스트 12개 통과. 회원가입·해시·중복·로그인, CRUD, 입력값 보존·자동 이스케이프, 기존 번호 보존, 404, 로그인 판정, 실제 HTTP 전송과 감시 DB 수집, 감시 서버 장애 시 게시판 응답 보존 확인.
- 브라우저: 틀린 비밀번호 실패 후 정상 로그인 → 기존 게시글 200 및 없는 게시글 404 접속 → 기록 새로고침 → 경로 검색·404 필터와 집계 비교 → 조건 해제.
- 브라우저: 메모 작성 → 목록·상세 반영 → 수정 중 취소해 원래 값 보존 → 공백 수정 오류와 입력값 보존 → 수정 저장 및 `완료` 상태 저장 → 새로고침 뒤 로그인·메모 유지.
- 브라우저: 별도 임시 메모 삭제 확인 → 취소 후 보존 → 다시 삭제 확인 → 확정 후 목록 및 상세 선택 갱신 → 메모 새로고침.

테스트는 UUID 이름의 임시 스키마를 만들고 제거합니다. 기존 운영 게시글·메모·사용자 자료를 지우지 않습니다.
