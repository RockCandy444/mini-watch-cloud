# 회원가입 구현하기

과제 원문: https://classroom.codemit.kr/classes/5/problems/22/submit

## 필수 체크리스트와 구현 위치

| 조건 | 구현 |
| --- | --- |
| 소스 문법 오류 없음 | Python 소스 AST 검사, 실제 PostgreSQL 통합 테스트 20개, Next.js 프로덕션 빌드 |
| 회원정보 암호화 저장 | 두 등록 API에서 Werkzeug `generate_password_hash(..., method="scrypt")` 실행. 비밀번호는 임의 salt를 포함한 단방향 해시로만 저장 |
| 회원정보 DB 저장 | PostgreSQL의 `users`, `monitor_users` 테이블에 영구 저장 |
| Python 사용 | `general/routes/auth.py`, `monitor/backend/routes/auth.py`의 Flask API |
| SQLAlchemy ORM 사용 | 각 서비스의 `models.py`, `db.py`, `repositories/users.py`. 모델 객체를 `Session.add()`로 저장하고 `select()`로 조회 |
| Next.js 프론트 | `monitor/frontend/package.json`, `next.config.mjs`, `src/app/`의 App Router 페이지 |
| 프론트·백엔드 모듈 분리 | 페이지 → 회원가입 컴포넌트 → API 모듈 / 라우터 → 공통 검증 → 사용자 저장소 → 모델·DB 세션 |

아이디는 로그인을 위한 식별자로 저장합니다. 비밀번호 원문은 저장하지 않으며 복호화 대신 해시 검증으로 로그인합니다.

## 계정 만드는 방법

README의 환경 준비 후 일반 API(5100), 감시 API(5200), Next.js(5173)를 실행합니다.
이미 준비된 환경이라면 두 Python 환경에서 변경된 `requirements.txt`를 다시 설치하고,
`monitor/frontend`에서 `npm ci`를 실행한 뒤 기존 Vite 대신 `npm run dev`를 실행하세요.

1. 대시보드: http://127.0.0.1:5173/register
2. 일반 게시판: http://127.0.0.1:5173/register/general
3. 영문·숫자·밑줄·하이픈으로 아이디 3~30자, 비밀번호 8~128자와 비밀번호 확인을 입력합니다.
4. 가입 완료 화면에서 해당 서비스의 로그인 화면으로 이동합니다.

두 계정은 서로 다른 DB에 저장됩니다. 같은 아이디를 각각 등록해도 됩니다.
대시보드 계정으로 일반 게시판에 로그인하거나 반대로 사용할 수는 없습니다.
기존 `create_user.py`로 만든 계정도 그대로 로그인됩니다.
회원가입은 계정 저장까지만 하고 로그인은 별도로 실행합니다.
일반 게시판 로그인은 기존 과제처럼 성공 판정을 표시하며, 대시보드 로그인은 세션을 생성합니다.
이 수업용 로컬 프로젝트에서는 대시보드 테스트 계정도 회원가입으로 생성합니다.

## API와 저장 흐름

| 프론트 경로 | Python API | 저장 테이블 |
| --- | --- | --- |
| `/api/auth/register` | 감시 Flask의 `POST /api/auth/register` | `monitor_users` |
| `/general-api/auth/register` | 일반 Flask의 `POST /auth/register` | `users` |

입력 JSON 필드: `username`, `password`, `password_confirm`.
성공 응답은 201과 `message`, `user: {id, username}`입니다. 비밀번호와 해시는 응답에 없습니다.
아이디의 앞뒤 공백만 제거하며 비밀번호 입력값은 바꾸지 않습니다.

- 잘못된 JSON·빈 입력·허용하지 않는 아이디·짧거나 긴 비밀번호·확인 불일치: 400.
- 중복 아이디: 409. 기존 계정의 비밀번호를 변경하지 않습니다.
- DB unique 제약으로 동시에 같은 아이디를 저장하려는 요청도 차단하고 트랜잭션을 롤백합니다.
- 허용하지 않은 Origin: 403. 기본 허용 화면은 `http://127.0.0.1:5173`입니다.
- DB 연결이나 준비 오류: 503. 화면은 입력을 보존하고 다시 시도하도록 안내합니다.

새 저장소 세션은 성공 시 커밋하고 예외 발생 시 롤백·종료합니다.
엔진에는 `hide_parameters=True`를 설정하고 오류 응답에 DB 접속 정보나 SQL을 넣지 않습니다.
회원가입 화면은 제출 중 중복 클릭을 막고, 성공 후 비밀번호 state를 비웁니다.
테이블 준비 SQL은 `IF NOT EXISTS`를 사용하고 기존 자료를 보존합니다.

## 검증 결과 (2026-10-07)

- 감시 통합 테스트 8개, 일반 게시판 통합 테스트 12개 모두 통과.
- 실제 PostgreSQL의 임시 스키마에서 ORM 저장·다시 조회·해시 검증·중복 가입·기존 로그인·입력 오류·출처 검사·DB 장애 검증.
- 기존 게시글 CRUD, 감시 기록, 메모 CRUD, 검색·필터·집계, 세션 보호 회귀 테스트 통과.
- Next.js 16.4.0 `npm run build` 성공: `/`, `/register`, `/register/general` 생성.
- 브라우저에서 비밀번호 확인 불일치, 중복 가입 안내·입력 보존, 대시보드 가입 → 로그인 → 로그아웃, 일반 게시판 가입 → 로그인 성공 확인.

검증용 스키마는 테스트 종료 후 제거합니다. 테스트 과정에서 기존 회원·게시글·메모는 수정하지 않습니다.
브라우저 검증으로 만든 `signup_ui_1007` 계정은 두 로컬 서비스에 남아 있습니다.

## 제출 파일

`package_signup.py`를 실행하면 프로젝트 상위 폴더에 `mini-watch-signup-submit.zip`을 만듭니다.
ZIP에는 앱 소스, 테스트, SQL, 안내 문서, 패키지 잠금 파일과 `.env.example`만 포함합니다.
실제 `.env`, 가상환경, `node_modules`, `.next`, 기존 빌드, Git 데이터와 로컬 로그는 제외합니다.
수업의 `try_*.py` 연습 스크립트도 실제 접속정보 혼입을 피하기 위해 ZIP에서 제외합니다.

강의실에서 **GitHub 저장소**를 선택하고 `https://github.com/RockCandy444/mini-watch-crud`를 입력하세요.
기본 브랜치 `main`에 회원가입 소스를 반영합니다. ZIP 형식으로도 제출할 수 있습니다.
온라인 채점 결과는 아직 확인하지 않았습니다.
