# Day2 배포 계획과 적용 결과

[과제 54](https://classroom.codemit.kr/classes/5/problems/54/submit). 작성·검증: 2026-10-13, Asia/Seoul.

## 저장소·시작 코드·진행 상태

본인 저장소: https://github.com/RockCandy444/mini-watch-cloud

작업·배포 브랜치: `day2-deploy`. 제출 편의를 위해 최종 파일을 `main`에도 동일하게 반영한다.
시작 코드는 [mini-watch-compose](https://github.com/RockCandy444/mini-watch-compose)의 `2e4b61d`이다.
공식 `zeroskill2400/mini-watch`의 `day07-cloud-materials`에서 `day2-materials/project-support/starter`를 가져와 비교했다.
기존 앱을 덮어쓰지 않고 Sentry 초기화·일반 세션 도우미·Next 프록시를 실제 앱에 적용했다.

**세 앱 모두 클라우드 미배포**이다. Render URL·Supabase 연결값·Sentry DSN을 확보하거나 원격 프로젝트를 생성하지 않았다.
Supabase 실제 접속, Render 재배포, Sentry 대시보드 오류 수신은 확인하지 않았다.
과제는 코드·설정·문서를 평가하며 실제 URL 접속이나 Sentry 수신을 필수로 요구하지 않는다.
이번 검증은 실제 Docker 이미지·별도 PostgreSQL 두 개·Next→Flask 요청·회귀 테스트·로컬 컨테이너 재생성이다.
로컬 DB 성공을 Supabase 접속 성공으로 표시하지 않는다.

## Render 무료 Docker 설정

Render Hobby workspace / Free instance, Supabase Free, Sentry Developer 범위로 진행한다. 결제·유료 전환은 사용하지 않는다.

| 앱 / 역할 | Root Directory | Dockerfile Path | Build Context | Docker Command | Health Check | 배포 브랜치 | Auto-Deploy | 상태 / 실제 URL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 감시 API / 로그인·기록·메모 | `monitor/backend` | `./Dockerfile` | `.` | 빈칸 | `/health` | `day2-deploy` | On Commit | 미배포 / 없음 |
| 일반 앱 / 로그인·게시글·기록 전송 | `general` | `./Dockerfile` | `.` | 빈칸 | `/health` | `day2-deploy` | On Commit | 미배포 / 없음 |
| 감시 화면 / Next 화면·프록시 | `monitor/next-frontend` | `./Dockerfile` | `.` | 빈칸 | `/` | `day2-deploy` | On Commit | 미배포 / 없음 |

감시 API → 일반 → Next 순서로 설정한다. Docker Command는 Dockerfile CMD를 쓰므로 비운다.
두 Flask는 `waitress-serve --host=0.0.0.0 --port=$PORT app:app`로 같은 전역 `app`을 읽는다.
개발 `python app.py`도 유지한다. 기본 포트는 일반 5100·감시 5200이며 환경의 PORT가 있으면 사용한다.
이미지의 PORT 기본값은 5000이고 Render가 지정하는 PORT가 이를 덮어쓴다.
감시 이미지는 자체 소스를 `/app/monitor/backend`에 복사하고 `PYTHONPATH=/app`로 기존 `monitor.backend.*` import를 보존한다.
기존 `common/registration.py`의 동일 사본을 각 Flask 빌드 폴더에도 포함하여 Root Directory 밖에 빌드가 의존하지 않는다.

Next는 `package-lock.json`으로 `npm ci` → `npm run build` → `npm run start -- --port $PORT` 순서다.
start는 `next start --hostname 0.0.0.0`이다. 기존 build-time rewrite를 제거하고 Route Handler가 요청 때 API 주소를 읽는다.
클라이언트 효과와 서버 프록시에서 실제 요청 시 데이터를 읽어 빌드에 외부 API·DB 응답을 요구하지 않는다.
실제로 MONITOR_API_URL·DB 설정이 없는 host/Docker production build가 모두 성공했다.

## 일반·감시 DB 구분과 SQL

| 앱 | Supabase 프로젝트 계획 | Session pooler | SQL / 테이블 |
| --- | --- | --- | --- |
| 일반 | 2·3교시 샘플을 일반용으로 재사용 | 그 프로젝트 Host, User `postgres.<GENERAL_PROJECT_REF>`, 5432 / postgres / require | `general/sql/deploy.sql`: users(id, username, password_hash), posts(id, title, body) |
| 감시 | 감시용 별도 Free 프로젝트 | 감시 프로젝트 Host, User `postgres.<MONITOR_PROJECT_REF>`, 5432 / postgres / require | `monitor/backend/sql/deploy.sql`: users, http_events, notes |

Host는 지역명을 조합하지 않고 각 프로젝트 Connect → Session pooler에서 복사한다.
두 DB 이름이 `postgres`여도 다른 프로젝트다. `DB_SSLMODE=require`로 SSL을 사용하고 transaction pooler 6543은 사용하지 않는다.
수업 구성에 따라 Data API를 끄고 Flask가 PostgreSQL에 직접 접속하도록 준비한다. 별도 RLS 정책은 추가하지 않는다.
이 원격 프로젝트 설정은 아직 실행하지 않은 절차다. 각 SQL Editor에 대응 deploy.sql을 적용한다.

두 앱의 psycopg CRUD와 SQLAlchemy 로그인·회원가입 모두 환경 DB 값과 SSL을 읽는다.
감시의 과거 monitor_users가 있고 users가 없으면 SQL은 테이블 이름만 변경해 ID·해시를 보존하고, 처음 설치면 users를 생성한다.
DROP·TRUNCATE·자료 삭제를 요구하지 않는다. 일반 SQL도 기존 게시글과 자동 번호를 유지한다.
감시 http_events는 id·occurred_at·method·path·status_code·event_type, notes는 id·title·body·status·created_at·updated_at이다.
게시글과 메모의 등록·조회·수정·삭제는 저장소 SQL에 연결되어 새로고침·앱 교체 후 DB에서 다시 읽는다. 서버 메모리 배열에 저장하지 않는다.

## 환경 변수·세션·비밀값

| 변수 | 대상과 역할 |
| --- | --- |
| DB_HOST·DB_PORT·DB_NAME·DB_USER·DB_PASSWORD·DB_SSLMODE | 각 Flask의 자기 DB. 배포 5432·postgres·require, local Compose는 각 DB 호스트·DB명·disable |
| SECRET_KEY | 각 Flask의 **서로 다른** 32자 이상 무작위 세션 서명 키. 재배포 후 동일 값을 유지 |
| SESSION_COOKIE_SECURE | local HTTP false, Render HTTPS true. HttpOnly·SameSite=Lax·앱별 쿠키 이름 유지 |
| EVENT_TOKEN | 일반 전송과 감시 확인에 **같은** 무작위 토큰. 두 세션 키와 별도로 생성 |
| MONITOR_URL | 일반 서버 전용: 감시 Flask HTTPS 주소 + `/api/events` |
| MONITOR_API_URL | Next 서버 전용: 감시 Flask HTTPS **기준 주소**, `/api/events`까지 넣지 않음 |
| FRONTEND_ORIGIN | Flask 출처 검사에 사용할 실제 감시 Next HTTPS origin |
| GENERAL_API_URL | 기존 일반 회원가입을 전달할 일반 Flask 기준 주소 |
| SENTRY_DSN | 각 Flask DSN. 제출 예시는 빈 값 |
| SENTRY_ENVIRONMENT | 일반 mini-general, 감시 mini-monitor |
| APP_VERSION | 배포 버전·커밋과 대응하는 Sentry release |
| ENABLE_SENTRY_TEST | 일반 실습 경로 활성화 여부. 최종 예시 false |
| PORT | 실행 환경의 바인딩 포트 |
| NEXT_PUBLIC_GENERAL_URL | 게시판 이동용 **공개 URL만** 빌드에 주입. 비밀값을 담지 않음 |

각 Flask와 Next에 `.env.example`을 따로 준비했다. 실제 .env는 각 앱 PC에서만 사용한다.
DB 비밀번호·세션 키·기록 토큰은 서버 설정이며 브라우저 코드·NEXT_PUBLIC_*에 넣지 않는다.
Git/Docker ignore는 실제 환경 파일·node_modules·.next·가상환경·캐시·DB 파일을 제외한다.
Compose의 classroom-... 값과 검증 계정은 disposable local fixture이며 원격 비밀값이 아니다. Render에는 별도 무작위 값들을 설정한다.

## 각 Flask 로컬 가상환경에서 계정 준비

각 DB의 deploy.sql 적용 후 다음을 **각 Flask 폴더에서 따로** 수행한다.

```powershell
# 일반은 프로젝트 루트에서 cd general
# 감시는 프로젝트 루트에서 cd monitor/backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# .env에 해당 앱 DB와 서버 설정을 채운 뒤:
.\.venv\Scripts\python.exe create_user.py
```

가상환경은 `general/.venv`·`monitor/backend/.venv`로 분리한다.
실제 비밀번호는 getpass로 입력하며 문서·콘솔에 적지 않는다. Werkzeug 해시만 각 DB users.password_hash에 저장한다.
동일 username이 있으면 기존 해시를 유지한다. `--classroom`은 local smoke용이며 원격 계정에는 사용하지 않는다.

## 로그인·기록·감시 요청 흐름

1. 일반 브라우저 → 일반 Flask `/auth/login` → 일반 users. 실패 401·성공 200. 성공은 일반 전용 세션 쿠키를 발급한다.
2. 일반 after_request → MONITOR_URL `/api/events`, method·path·status JSON + X-Event-Token. 요청 본문·비밀번호를 기록으로 보내지 않는다.
3. 감시 Flask가 EVENT_TOKEN을 상수 시간 비교. 잘못된 토큰 403·잘못된 기록 400. POST `/auth/login` 401은 login_failure, 200은 login_success로 분류해 http_events에 저장한다.
4. 감시 브라우저 → 같은 Next origin `/api/...` → Next 서버 Route Handler → MONITOR_API_URL의 감시 Flask → 감시 DB. 로그인된 GET 조회로 기록 종류·상태 코드를 화면에 표시한다.

기존 src/app 구조를 유지하므로 과제의 app/api/[...path]/route.js에 대응하는 실제 파일은 **monitor/next-frontend/src/app/api/[...path]/route.js**이다.
프록시는 Cookie·Content-Type·X-CSRF-Token, query·본문·method를 전달하고 응답의 여러 Set-Cookie·Content-Type·HTTP 상태를 보존한다.
no-store를 적용하고 화면의 허용된 경로만 전달한다. 브라우저 POST `/api/events`는 404로 거부하며 서버 이벤트 토큰을 브라우저에 주지 않는다.
로그인·/auth/me의 csrf_token은 src/api/client.js가 메모리에 두고 메모 변경·로그아웃 헤더로 전달한다. 새로고침 때 /auth/me로 다시 읽는다.
Flask는 세션에 일치하는 CSRF 값을 확인한다. 기존 일반 회원가입도 제한된 `/general-api/auth/register` → 감시 Flask → GENERAL_API_URL로 유지한다.

## Compose와 Render 차이·health 범위

두 Compose 및 기존 `gateway/general.conf`·`gateway/monitor.conf`는 **로컬 실행 자료**다. 기존 gateway 폴더명을 유지했다.
local 프로젝트 m5d2-general·m5d2-monitor, gateway 8081·8082, PostgreSQL named volume 두 개를 사용한다.
공유 외부 망 m5d1-events에는 두 API만 참여하고 이벤트 URL은 http://monitor-api:5000/api/events이다.
감시 gateway는 API도 Next로 보내므로 local에서도 Route Handler를 거친다. DB는 자기 API의 data 내부 망에만 있고 PC 포트를 공개하지 않는다.
Render는 Compose·Nginx·local DB를 실행하지 않고 각 앱 Dockerfile로 별도 서비스를 실행하며 HTTPS 주소·외부 Supabase 연결을 설정한다.
두 Flask `/health`는 **liveness** 확인이다. DB 접속·사용자 조회·테이블·로그인 성공을 증명하지 않는다. 실제 기능과 SQL 행 조회는 별도로 확인한다.

## 오류 재현·수정 커밋과 절차

| 단계 | 실제 SHA | 변경 |
| --- | --- | --- |
| 적용·재현 | 192144ba4e564d671e756d2a5948a3f70f032cf0 | 배포·SSL·세션·토큰·Sentry·Next 적용. 활성·로그인 후 general/app.py의 sentry_test()에서 1/0 → ZeroDivisionError / 500 |
| 수정 | 853988babef60cd36316058c26ea78f5d3aab7f4 | 같은 함수의 1/0 → 1/1, 정상 JSON result 1.0 / 200. 로그인·feature flag 유지, 보호·정보 제외 검증 추가 |

두 SHA의 [실제 diff](verification/sentry-fix.diff)와 전체 Git 이력을 함께 제공한다.
재현 이미지는 비활성 404·미로그인 401·활성 로그인 500을 실제 확인했고, 최종 이미지는 같은 조건에서 200과 result 1.0을 확인했다.
분모 0이 원인이고 분모 1로 수정했다. 경로 삭제·예외 숨기기·SDK 비활성화로 회피하지 않는다.
api_access_error()·ENABLE_SENTRY_TEST 조건, configure_errors('mini-general'), 로그인·게시글·기록 전송은 유지한다.
Sentry DSN이 없어 실제 수신은 확인하지 않았으며 SDK 옵션·이벤트 정보 제거를 테스트했다.

배포 시 ENABLE_SENTRY_TEST를 잠시 true로 하고 배포 완료 후 일반 계정으로 로그인해 같은 경로를 확인한다.
코드를 수정한 뒤 git add → commit → push origin day2-deploy → Render 배포 SHA 확인 → 같은 기능 재확인 순으로 진행한다.
배포 SHA가 수정 커밋 또는 그 후손인지 확인하고 게시글·메모·새 실패/성공 기록도 점검한다.
마지막에 **false로 되돌리고** 배포 완료 후 해당 경로 404를 확인한다.
Sentry **Resolve는 코드 수정이나 재배포를 대신하지 않는다**. 이전 코드가 실행되면 오류는 다시 발생한다.
재배포 뒤 기존 게시글·메모를 읽어 이미지 코드와 DB가 별도로 보관됨을 확인한다. local에서는 모든 컨테이너 재생성 뒤 자료·세션 유지를 실제 검증했다.

## 선택 1: 설정 오류 진단

| 증상 | 제출 코드의 처리 / 먼저 확인할 설정·로그 |
| --- | --- |
| 화면 503 MONITOR_API_URL 설정 안내 | Next Route Handler의 기준 주소 미설정 분기. Next 서버 환경 변수 확인 |
| 화면 502 감시 API 연결 실패 | Next fetch URL·연결·15초 timeout catch. HTTPS 기준 주소·감시 Render 상태·Next 로그 확인, 감시 /health 직접 확인 |
| 일반 기능 정상인데 기록 없음 | request_logging.py의 전송 실패 경고. MONITOR_URL의 `/api/events` suffix, 감시 상태, 감시 403이면 두 EVENT_TOKEN 대응 확인. 전송 실패로 일반 응답을 깨지 않음 |
| 로그인·게시글·메모 503 | 각 Flask의 psycopg/SQLAlchemyError 처리. General/Monitor database request failed: 예외 종류 로그. 자기 DB_HOST·PORT·NAME·USER·PASSWORD·SSLMODE 및 deploy.sql 대응 확인. 비밀 연결 문자열 출력하지 않음 |
| 입력 400 | post_rules.py·validate_note()·로그인 검사·make_event(). 공백·JSON·메서드·처리 상태·코드 입력을 수정. DB 인증 오류와 구분 |
| 보호 401 / 403 | 미로그인·만료 쿠키 / CSRF·이벤트 토큰·Origin. auth/me·새 로그인과 Cookie/Set-Cookie/X-CSRF-Token 전달 확인 |
| 404 | 없는 자료·불허 프록시 경로·비활성 실습 경로 구분. health 성공만으로 DB 준비를 판단하지 않음 |

## 선택 2: 연결 실패 안내·재시도

프록시는 API 응답의 400·401·403·503을 그대로 전달한다. 연결 실패는 **502**와 `감시 API에 연결하지 못했습니다. /health와 MONITOR_API_URL을 확인해 주세요.`이다.
기준 주소 미설정은 503이다. src/api/client.js는 error JSON과 status를 ApiError로 전달하고 브라우저 자체 fetch 실패는 status 0으로 구분한다.
App.jsx → LoginForm의 **연결 다시 확인** 버튼이 auth/me를 재요청한다.
EventsPanel의 **기록 새로고침**·NotesPanel의 **메모 새로고침**은 데이터를 재조회한다.
finally에서 busy/loading을 해제하므로 실패 후 버튼이 다시 활성화되며 role=alert 안내를 유지한다.
실제로 감시 API 중지 시 Next 502 안내와 복구 후 같은 요청 200을 확인했다.

## 선택 3: Sentry 정보 제외

두 observability.py는 지원 코드의 설정을 유지한다. send_default_pii=False는 기본 개인정보 전송을 끈다.
include_local_variables=False는 스택 로컬 변수에 포함된 비밀번호·키를 제외하고 max_request_body_size='never'는 요청 본문 수집을 끈다.
traces_sample_rate=0.0으로 이번 과제의 tracing을 끈다. before_send=remove_request_secrets는 request의 data·cookies·headers·query_string과 최상위 user를 제거한다.
본문에는 비밀번호, 쿠키에는 세션, 헤더에는 CSRF/이벤트 토큰, 쿼리에는 검색 정보, user에는 사용자 식별 정보가 있을 수 있어 마지막 필터도 적용한다.
service tag/environment로 mini-general·mini-monitor를 구분한다. 빈 DSN이면 초기화를 생략한다.

## 선택 4: 오류 수정 비교·기존 기능

위 전후 SHA와 sentry-fix.diff의 핵심은 `result = 1 / 0` → `result = 1 / 1`로 활성·로그인 요청을 500에서 200으로 바꾸는 것이다.
로그인 gate·실습 flag·SDK 초기화·게시글·감시 기능은 diff에서 제거하지 않는다.
기존 일반 12개·감시 14개 회귀 테스트와 Sentry 2개, HTTP smoke 검증을 통과했다.
실제 결과는 [verification/cloud-results.md](verification/cloud-results.md), 항목 대응은 [CHECKLIST.md](CHECKLIST.md)에 있다.

## 참고

[Supabase 공식 PostgreSQL 연결](https://supabase.com/docs/guides/database/connecting-to-postgres),
[Next Route Handlers](https://nextjs.org/docs/app/api-reference/file-conventions/route), [Next 배포](https://nextjs.org/docs/app/getting-started/deploying)를 참고했다.
Next 16.4.0 설치 패키지 next/dist/docs의 route·환경 변수·배포 가이드도 읽어 async params와 서버 실행에 적용했다.
