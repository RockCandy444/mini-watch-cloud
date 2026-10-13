# 과제 54 체크리스트: 필수 20 / 선택 4

[과제 원문](https://classroom.codemit.kr/classes/5/problems/54/submit)의 코드·설정·문서 평가 기준에 대응한다.
완료 표시는 구현과 검증 기준이다. Render·Supabase 실제 배포와 기능 검증도 완료했으며, 실제 Sentry 수신은 아직 설정하지 않았다.
진행 상태는 [LIVE_DEPLOYMENT.md](LIVE_DEPLOYMENT.md)와 [deployment-plan.md](deployment-plan.md)에 명시했다. Classroom 채점을 대신하는 자체 결과로 표시하지 않는다.

| 필수 | 확인 | 실제 파일·근거 |
| --- | --- | --- |
| 1. 세 앱 소스·의존성·역할과 변경 설명 | [x] | general/, monitor/backend/, monitor/next-frontend/ 및 requirements.txt·package.json/lock, README의 앱 역할·변경 표 |
| 2. 두 Flask Dockerfile·Waitress·0.0.0.0·PORT·같은 app | [x] | 앱별 Dockerfile의 pip/COPY 및 waitress-serve app:app, 개발용 app.py 유지. 두 이미지 실제 빌드·Waitress 실행 |
| 3. Next 설치·production build·서버 실행·빌드 외부 요청 불필요 | [x] | npm ci → npm run build → npm run start, start=next start. env 없는 host/Docker build 성공, Route Handler 요청 때 API 접속 |
| 4. 앱별 Root·Dockerfile·브랜치·Health와 무료 Render 설정 | [x] | deployment-plan.md·LIVE_DEPLOYMENT.md의 실제 Free·context .·Command 빈칸·수동 배포 및 On Commit 권장 구분 |
| 5. 두 Flask /health와 DB 확인 구분 | [x] | 두 app.py의 /health, monitor health 회귀 테스트, 문서의 liveness와 실제 DB 조회 구분 |
| 6. DB 환경 변수 6개 일치 | [x] | 각 db.py의 DB_HOST·PORT·NAME·USER·PASSWORD·SSLMODE. psycopg와 SQLAlchemy 모두 SSL 적용, 각 예시·문서 대응 |
| 7. 별도 Supabase 프로젝트·Session pooler | [x] | 각 .env.example·배포 계획의 일반 샘플/감시 별도 프로젝트, Host/User 대응, 5432·postgres·require |
| 8. users/posts 및 users/http_events/notes 배포 SQL·자료 보존 | [x] | 두 sql/deploy.sql, users ORM와 기존 CRUD SQL 일치. 감시 monitor_users 이름 변경 이행·IF NOT EXISTS. DROP/TRUNCATE 없음 |
| 9. 예시 설정·비밀값 제외·ignore | [x] | 세 .env.example, 빈 SENTRY_DSN·자리표시자, .gitignore·앱별 .dockerignore의 환경 파일·생성물 제외 |
| 10. 계정 준비·해시·앱별 로컬 가상환경 안내 | [x] | 두 create_user.py → 각 users 저장소 → password_hash, getpass. 배포 계획의 general/.venv·monitor/backend/.venv 안내 |
| 11. 세션 env·앱별 키·HTTP/HTTPS | [x] | general/auth_helpers.py·monitor/backend/app.py, SECRET_KEY·SESSION_COOKIE_SECURE, 다른 이름/키. false/true 설정 문서 |
| 12. MONITOR_URL·EVENT_TOKEN·서버 전송/확인 | [x] | general/request_logging.py X-Event-Token 전송, monitor/routes/events.py hmac 비교, 두 예시와 문서. Next 브라우저 ingestion 차단 |
| 13. 로그인 실패/성공 분류·DB·화면 | [x] | make_event(): login_failure/401·login_success/200, repositories/events.py, EventsPanel 종류·코드 열. HTTP smoke 실제 조회 |
| 14. 브라우저 /api·서버 Route Handler·MONITOR_API_URL | [x] | src/api/client.js와 src/app/api/[...path]/route.js. 기존 src/app 구조의 과제 app/ 대응을 문서에 명시 |
| 15. Cookie·CSRF·Set-Cookie·상태 전달 | [x] | Route Handler 헤더/상태 보존, client.js csrf_token 저장·헤더, Flask 세션 검증. 로그인/메모 smoke 검증 |
| 16. 게시글·메모 CRUD를 각 DB·화면에 연결 | [x] | 각 routes/repositories·Jinja/NotesPanel. 두 실제 DB 행 확인·변경·삭제, 컨테이너 재생성 후 조회 |
| 17. 두 Flask Sentry SDK·앱 시작 env 초기화 | [x] | requirements sentry-sdk[flask], observability.py, create_app()에서 configure_errors. app:app import에도 실행. DSN/env/version을 환경에서 읽음 |
| 18. 정상 sentry-test·로그인·flag·최종 false | [x] | general/app.py sentry_test() 1/1 정상 JSON, api_access_error/flag 유지. 예시 false. 실제 404·401·500→200 검증 |
| 19. 주소 흐름·local Compose·커밋/push/배포 확인·경로 비활성 | [x] | deployment-plan.md 요청 흐름·Compose 차이·배포 SHA 점검·동일 요청 확인 후 false 복구 절차 |
| 20. 이번/오류 수정 SHA·파일·원인·수정 일치 | [x] | README·배포 계획·GIT_WORK.md, 6d14279→979f7da 및 verification/sentry-fix.diff. 실제 배포 URL·검증과 Sentry 수신 미확인을 구분 |

| 선택 | 확인 | 실제 파일·근거 |
| --- | --- | --- |
| 1. API 주소·DB·입력 오류 진단·health 한계 | [x] | 배포 계획 선택 1의 코드 처리·상태·설정/로그 표, Flask error handler·입력 검사·proxy 분기 |
| 2. 프록시 실패 안내·화면 재시도·코드 일치 | [x] | 502/503·ApiError·LoginForm 연결 다시 확인·EventsPanel/NotesPanel 새로고침. API 중지/복구 HTTP 확인 및 화면 확인 |
| 3. Sentry 본문·쿠키·헤더·사용자 정보 제외·설명 | [x] | 두 observability.py before_send·send_default_pii·include_local_variables·max_request_body_size, 선택 3 설명·검증 |
| 4. 수정 전후 SHA·diff·효과·기존 기능 유지 | [x] | 배포 계획 선택 4, 두 실제 SHA·sentry-fix.diff·보호/회귀 검증. 1/0→1/1 외 기존 경로·SDK 유지 |

검증 요약: [로컬 결과](verification/cloud-results.md), [실제 배포 결과](verification/public-results.md).
이전 Day1 evidence/와 기능 가이드는 과거 참고 자료다.
