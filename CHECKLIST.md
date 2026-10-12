# 과제 51 체크리스트

2026-10-12 실제 Docker 실행으로 **필수 20개·선택 4개**를 확인했습니다.
근거는 소스 설정, 실제 명령 출력, 브라우저 화면 및 GitHub PR입니다. 강의실에는 제출하지 않았습니다.

## 필수 20개

| 완료 | 요구사항 | 구현·실제 증거 |
| --- | --- | --- |
| [x] | 일반·감시 프로젝트 이름과 실행·종료 분리 | compose-general.yaml의 m5d1-general, compose-monitor.yaml의 m5d1-monitor, evidence/recreate.txt의 각각 up/down |
| [x] | 일반 PostgreSQL·Flask·gateway 실행 | compose-general.yaml, evidence/initial.txt·postmerge.txt의 ps |
| [x] | 감시 PostgreSQL·Flask·Next.js·gateway 실행 | compose-monitor.yaml, evidence/initial.txt·postmerge.txt의 ps |
| [x] | Flask Dockerfile·0.0.0.0:5000 | general/Dockerfile, monitor/backend/Dockerfile, API logs |
| [x] | Next.js 이미지 production build·빌드 결과 실행 | monitor/next-frontend/Dockerfile의 npm run build·standalone server.js, initial.txt 빌드·gateway 화면 |
| [x] | 빌드 context의 .dockerignore | 루트 및 monitor/next-frontend/.dockerignore에 venv·node_modules·.next·.env·캐시 제외 |
| [x] | 두 gateway만 PC 공개 포트 | Compose ports 8081·8082, 실제 ps; API·웹·DB는 내부 포트만 표시 |
| [x] | DB는 자기 API와 내부 망, 공유 망 제외 | general-data·monitor-data 내부 망; network.txt의 DB 이름 조회 비교 |
| [x] | 같은 실제 external 공유 망과 두 API 참여 | 양쪽 external/name m5d1-events; inspect에 API 2개만 존재 |
| [x] | API별 자기 DB 주소·계정·내부 포트 일치 | Compose DB_HOST·DB_PORT·DB_NAME·DB_USER·DB_PASSWORD와 DB 설정 |
| [x] | 일반→감시 서비스 이름·내부 포트 전송 | MONITOR_URL=http://monitor-api:5000/api/events; getent 및 실제 401/200 기록 |
| [x] | DB healthcheck·API 준비 대기, 감시 준비 후 로그인 | 양쪽 service_healthy; initial.txt에서 감시 로그인·/api/auth/me 200 확인 후 일반 시작 |
| [x] | 초기 SQL·데이터 볼륨 | 두 DB 초기 SQL mount·named volumes; recreate.txt 데이터 전체 비교 |
| [x] | 일반 gateway 로그인 후 기존 게시글 화면 | general-login.jpg, general-board.jpg, 실제 HTTP 200 |
| [x] | 새 실패·성공의 기록 종류와 코드가 감시 화면에 표시 | login-events.jpg의 이번 로그인 #8 login_failure/401, #9 login_success/200 |
| [x] | 화면에서 새 메모 저장·새로고침 후 조회 | note-refreshed.jpg, 메모 #1 Docker 점검·로그인 실패와 성공을 확인했다 |
| [x] | -v 없는 두 Compose 종료·재실행 후 자료 유지 | recreate.txt에서 기록 11개·메모 상세 전후 정확히 동일, note-after-recreate.jpg |
| [x] | config·ps·inspect·이름 조회 실제 결과와 확인 범위 구분 | initial.txt·postmerge.txt, README의 DNS·앱 응답·SQL 확인 범위 설명 |
| [x] | Docker 적용 Git 커밋·식별자·변경 내용 | GIT_WORK.md의 95bf251·113a708·80f008a·f2db339, GitHub main |
| [x] | 소스·설정·README 포함, 준비→실행→확인→종료 재현 | README 명령, 세 Dockerfile, SQL·Nginx·requirements·package-lock·실제 증거 |

## 선택 4개

| 완료 | 요구사항 | 실제 증거 |
| --- | --- | --- |
| [x] | 공유 망 분리·복구, DNS·기록 전달 차이 및 새 기록 복구 | network.txt: 분리 중 monitor-api 조회 exit 2·기록 14개 유지, Compose 복구 후 새 #15~17 수집 |
| [x] | Flask 소스 변경 후 restart/rebuild와 소스·이미지·컨테이너 비교 | rebuild.txt: restart는 기존 문구·동일 ID, rebuild는 새 문구·새 이미지/컨테이너 ID |
| [x] | 자기 DB·다른 DB 조회와 망 설정·확인 범위 설명 | network.txt: general-db=172.24.0.2, monitor-db=exit 2; README에서 DNS와 DB 인증·SQL 구분 |
| [x] | 실제 Docker 개선을 작업 브랜치·PR 검토·병합하고 재확인 | PR #1 MERGED, pr-diff.txt·pr-result.json·final.txt·postmerge.txt, GIT_WORK.md |

PR: https://github.com/RockCandy444/mini-watch-compose/pull/1

제출 저장소: **https://github.com/RockCandy444/mini-watch-compose**
