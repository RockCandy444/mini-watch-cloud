# Day3 — 실제 요청 로그와 검토 후보의 근거

[Codemit 55번 과제](https://classroom.codemit.kr/classes/5/problems/55/submit)의 필수 20개·선택 4개를 기존 일반 게시판과 감시 프로젝트에 적용했다. 항목별 파일 대응은 [DAY3_CHECKLIST.md](DAY3_CHECKLIST.md)에서 확인한다. Classroom 최종 제출은 사용자가 직접 진행한다.

## 1. 구성·개념 설명

시작 자료는 직전 Day2 프로젝트 `mini-watch-cloud`의 `day2-deploy` 작업 폴더이다. 수업 원형은 zeroskill2400/mini-watch이며, 과거 `m5d3-solution` 코드로 덮어쓰지 않고 이번 미션의 규칙을 구현했다. 일반/감시 소스, Dockerfile, 두 Compose, `gateway/`, 의존성과 npm 잠금 파일, 기존 SQL·계정·게시글·메모를 유지했다. 직전 배포 문서는 DAY2_README.md에 보관했고 이번 로컬 실행은 이 README를 기준으로 한다. 새 앱·새 클라우드 서비스·DB 초기화·새 브랜치를 만들지 않는다.

| 이번 변경 파일 | 역할 / 수업 파일 대응 |
| --- | --- |
| monitor/backend/event_rules.py, routes/events.py | make_event 분류를 분리하고 post_list/request_error 추가; 기존 토큰 검증·로그인 분류 유지 |
| monitor/backend/learning/capture_case.py | 로컬 일반 서비스에 실제 GET 목록/없는 경로 요청, 시작 ID 이후 DB 행 검증·출력 |
| learning/normalize.py, http_rules.py | 원본 복사·http-ID 정규화, 네 조건 조회 선택, >= 비교, 뒤따른 404 문맥 |
| learning/support.py, report.py | 동일 observation.json 읽기, DB 관찰 구간 읽기, 실제 HTTP 카드 한 개 |
| learning/lesson2.py~lesson5.py | 읽기→정규화→선택→비교→문맥 연결한 파일 실습 |
| monitor/backend/routes/analysis.py, app.py | 로그인 보호된 관찰 시작/분석 API 등록, 인수 검증 |
| monitor/next-frontend/src/components/AnalysisClient.js, Dashboard.jsx, src/style.css | 새 관찰·기준·결과·원본 근거 표를 기존 대시보드에 연결 |
| monitor/next-frontend/src/app/api/[...path]/route.js | 서버 API 프록시에 읽기 전용 analysis 경로 허용, 기존 세션·CSRF 전달 유지 |
| compose-monitor.yaml | learning/routes/event_rules 읽기 전용 바인드, GENERAL_API_URL 지정 |
| learning/educational_pcap.py, educational_ioc.py | 실제 HTTP 카드와 독립된 두 교육 실습 |
| .gitignore, monitor/backend/.dockerignore | 생성 원본 JSON·PCAP·캐시·실제 .env 제외 |
| monitor/backend/tests/test_analysis.py | 순수 함수·시간 경계·근거 일관성 검증; 합성 테스트 행은 실제 요청 결과가 아님 |

### 요청이 기록과 화면이 되는 경로

1. 일반 `general/app.py:create_app`이 `register_request_logging(app)`을 호출한다. `general/request_logging.py:register_request_logging`의 **app.after_request(record_request)**가 응답 후 기록 함수를 연결한다.
2. `record_request(response)`가 request.method·request.path·response.status_code를 딕셔너리로 만든다. `print`는 일반 컨테이너 표준 출력에 JSON을 남긴다. 별도의 `requests.post`가 서버 설정 MONITOR_URL로 JSON과 X-Event-Token을 전송한다. 출력 성공은 전송·저장 성공과 다르다. health 점검은 기록에서 제외한다. 전송 실패는 경고를 남기고 일반 응답을 유지하며 재전송하지 않는다.
3. 감시 `routes/events.py:receive`가 EVENT_TOKEN을 상수 시간 비교한다. `event_rules.py:make_event`는 GET / 200을 post_list, 없는 경로 404를 request_error로 분류한다. 기존 로그인 성공·실패 분류도 유지한다. 외부가 임의로 보내는 event_type은 믿지 않는다.
4. `repositories/events.py:create_event`가 파라미터 SQL로 http_events에 저장한다. `sql/prepare_monitor.sql`의 IDENTITY가 숫자 ID를, occurred_at DEFAULT NOW()가 **감시 DB 수신·저장 시각**을 붙인다. 클라이언트 요청 시작시각이 아니다. SQL 초기화 파일을 기존 DB에 재실행할 필요는 없다.
5. `normalize_event`가 원본을 복사하여 id를 http-원본ID, source를 http_live, kind를 event_type으로 대응시킨다. 방법·경로·상태를 유지하고 수신시각은 같은 순간의 UTC ISO 표현으로 직렬화한다. 사용자·IP 필드를 만들지 않는다. 404도 정규화에 남긴다.
6. `select_views`가 GET·/·200·post_list 네 조건을 모두 충족하는 행 목록을 반환한다. **그 목록**에서 횟수와 조회 ID를 구한다. `analyze_http`의 판정은 `len(views) >= threshold`이다.
7. `find_following_errors`는 정렬 상태와 관계없이 선택된 조회 중 마지막 수신시각을 구하고 **전체 정규화 행**에서 404이며 `0 < gap <= 30`인 행을 고른다. 조회가 없으면 오류 목록도 빈다. 404는 조회 횟수에 더하지 않고 근거에만 붙인다.
8. `support.current_boundary`는 현재 MAX(id)를 읽는다. `read_recent`는 `id > after_id` **및** `reference_time - 60초 <= occurred_at <= reference_time`으로 조회한다. ID의 기존 기본키 인덱스를 활용하는 파라미터 쿼리이며 첫 결과의 reference_time은 DB clock_timestamp로 정한다. 새 관찰 버튼은 60초 자동 수집 타이머가 아니다.
9. `build_report`는 실제 HTTP 카드 **한 개**에 관찰값·비교 기준·판정·이유·evidence ID·records 원본 대응 행을 만든다. `AnalysisClient.js`는 ID·UTC 수신시각·방법·경로·상태·종류 표를 보여 주고 404를 구분한다. http- 뒤 숫자는 DB ID이다.
10. 기준 10→20 변경에는 같은 after_id와 reference_time을 다시 보낸다. 첫 조회 이후 기록은 그 기준시각보다 늦으므로 들어오지 않는다. 새 관찰은 이전 결과·기준시각·ID 상태를 비우고 새 경계를 읽는다. 이전 DB 행을 DELETE하지 않는다. API는 기존 require_login과 세션 보호를 유지하고 기준/ID의 정수·범위 및 중복 인수, 기준시각의 시간대·형식·미래 여부를 검증한다.

조회 12회와 404 한 건이면 **관찰값 12·근거 13행**이다. 기준 10은 검토 후보이고 같은 자료의 기준 20은 기준 미해당이다. 근거 13은 통제한 사례의 예상이며 모든 상황에 고정하지 않는다. 같은 서비스에서 시간상 뒤따랐다는 범위만 말한다. 같은 사용자·같은 IP·인과관계·침해 확정을 주장하지 않고 기준 미해당을 정상 입증이라고 쓰지 않는다. PCAP·IOC 자료를 HTTP 보고서에 넣지 않는다.

## 2. 실행 방법

### 기존 서비스·계정·설정 준비

Docker Desktop Linux 엔진을 켜고 **이 README와 두 Compose가 있는 기존 폴더의 Windows CMD**에서 실행한다. 이미 있는 폴더를 다시 복제하지 않는다. 일반 8081·감시 8082 공개 포트를 사용한다. 두 DB의 m5d2 named volume과 m5d1-events 외부 망을 그대로 유지한다. 망이 없을 때에만 `docker network create m5d1-events`를 실행한다.

```bat
docker compose -f compose-monitor.yaml config --quiet
docker compose -f compose-general.yaml config --quiet
docker compose -f compose-monitor.yaml up -d --build
docker compose -f compose-general.yaml up -d --build
```

감시 http://localhost:8082 에 **기존 계정**으로 로그인한다. 일반 http://localhost:8081 의 기존 게시글을 확인한다. 계정이 없는 경우에만 아래 interactive 명령에서 본인의 실습 아이디와 비밀번호를 입력한다. 기존 아이디를 덮어쓰지 않는다. 화면의 회원가입도 그대로 사용할 수 있다.

```bat
docker compose -f compose-monitor.yaml exec monitor-api python create_user.py
docker compose -f compose-general.yaml exec general-api python create_user.py
```

| 설정 | 연결과 역할 |
| --- | --- |
| 일반 MONITOR_URL | http://monitor-api:5000/api/events, 외부 공유 망의 감시 수신 API |
| 양쪽 EVENT_TOKEN | 일반 X-Event-Token과 감시 검증 값이 같아야 함; 서버에서만 사용 |
| 감시 GENERAL_API_URL | http://general-api:5000, 로컬 실습 요청 및 기존 일반 회원가입 전달 |
| 감시 web MONITOR_API_URL | http://monitor-api:5000, Next 서버의 API 프록시 주소 |
| 각 API DB_HOST/PORT/NAME/USER/PASSWORD/SSLMODE | 자기 DB 망의 별도 PostgreSQL, 로컬 sslmode disable |
| 각 SECRET_KEY / SESSION_COOKIE_SECURE | 기존 별도 세션 키, 로컬 HTTP secure=false |
| FRONTEND_ORIGIN | http://localhost:8082, 기존 출처 확인 |

Compose에는 기존 **로컬 교육 전용 예시 값**을 유지했다. 운영에 안전한 값이라는 뜻이 아니며 운영 비밀값·실제 .env·개인 비밀번호·키·토큰은 제출/브라우저 코드에 넣지 않는다. 이번에는 배포하거나 클라우드 환경 설정을 바꾸지 않는다.

### 최신 코드 적용

이번 최초 적용에는 위 up --build로 API·web 이미지를 모두 적용한다. 이후 learning/routes/event_rules 변경은 읽기 전용 연결에서 읽으므로 API restart로 적용한다. app.py·Dockerfile·requirements 변경은 API rebuild가 필요하다. Next 화면은 이미지의 COPY 소스이므로 반드시 web rebuild가 필요하다. gateway restart는 재생성된 upstream IP를 다시 읽는다.

```bat
docker compose -f compose-monitor.yaml restart monitor-api
docker compose -f compose-monitor.yaml up -d --build monitor-web
docker compose -f compose-monitor.yaml restart monitor-gateway
```

### 실제 4회 파일 실습

각 명령 성공 후 다음 명령으로 넘어간다. capture는 실제 HTTP 요청 후 이번 시작 ID 이후 DB 행이 정확히 일치할 때만 JSON을 출력한다. 다른 탭에서 일반 페이지를 새로고침하지 않는다.

```bat
if not exist monitor\backend\learning\data mkdir monitor\backend\learning\data
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.capture_case 4 > monitor\backend\learning\data\observation-next.json && move /Y monitor\backend\learning\data\observation-next.json monitor\backend\learning\data\observation.json
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.lesson2
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.lesson3
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.lesson4
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.lesson5
```

`-T`는 터미널 장식을 뺀다. `>`는 PC 임시 파일에 출력한다. `&& move /Y`는 성공한 캡처만 observation.json으로 교체한다. 컨테이너 learning은 읽기 전용이다. lesson2~5는 모두 같은 observation.json을 읽으며 JSON은 제출하지 않아도 생성할 수 있다. 실패 후 남은 이전 파일을 이번 결과로 해석하지 않는다. PowerShell에서 실행하려면 해당 CMD 명령을 cmd /c로 실행하거나 종료코드 0을 확인한 뒤 UTF-8 파일 저장·교체를 각각 수행한다.

### 실제 12회 화면 실습과 기준 비교

1. 감시 화면에서 기준 10을 입력하고 **새 관찰 시작**을 누른다.
2. 아래 실제 요청 캡처 명령을 실행한다. 다른 일반 요청은 보내지 않는다.

```bat
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.capture_case 12 > monitor\backend\learning\data\observation-next.json && move /Y monitor\backend\learning\data\observation-next.json monitor\backend\learning\data\observation.json
```

3. 캡처 성공 뒤 **1분 안에 첫 결과 불러오기**를 누른다. 근거 보기를 펼쳐 조회 12행과 뒤따른 404 한 행을 구분한다.
4. 새 관찰을 시작하지 않고 **기준만 20**으로 바꿔 결과를 불러온다. 관찰값·after_id·reference_time·근거 ID는 같고 판정만 달라진다. 기준 10으로 복구해 다시 불러온다.
5. 마지막으로 새 관찰 시작을 누르고 일반 요청을 만들지 않은 채 결과를 불러온다. 관찰값 0·근거 없음이며 DB 과거 기록은 남는다. ID 경계 때문에 이전 행을 선택하지 않은 것이다.

화면은 JSON 파일이 아니라 감시 DB를 읽는다. 파일과 화면의 읽는 곳은 다르지만 위 실습에서는 같은 실제 요청에서 생성된 행을 사용한다.

### 실패와 재시도

예상과 다른 개수, 캡처 오류, 첫 조회까지 60초 경과가 있으면 전송 경고와 감시 로그를 확인한다. 실패한 파일 분석을 이어 실행하지 않는다. 원인 해결 뒤 **새 관찰 시작→캡처→즉시 첫 결과**로 다시 한다. DB·볼륨 삭제나 JSON 숫자 수정으로 개수를 맞추지 않는다.

```bat
docker compose -f compose-general.yaml logs --tail 20 general-api
docker compose -f compose-monitor.yaml logs --tail 20 monitor-api
docker compose -f compose-monitor.yaml exec monitor-db psql -U monitor -d monitor_db -c "SELECT id, occurred_at, method, path, status_code, event_type FROM http_events ORDER BY id DESC LIMIT 15;"
```

이번 기존 DB 사용자는 수업 예시 sample이 아니라 **monitor**이다. SELECT의 숫자 ID를 근거 http-ID와 대조하고 이전 행 보존을 확인한다. 종료가 필요하면 down에 -v를 붙이지 않는다.

### 선택 1: 교육용 PCAP 독립 실습

`learning/educational_pcap.py`는 표준 라이브러리로 Ethernet/IPv4/UDP 패킷 8개를 **교육용으로 생성**하고 PCAP에 저장·다시 읽는다. 네트워크를 캡처하지 않으며 게시판의 실제 패킷이 아니다. 기본 출력 경로를 읽기 전용 learning 대신 /tmp로 지정한다.

```bat
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.educational_pcap --path /tmp/day3-educational.pcap
```

첫 패킷 기준 `0 <= delta < window`의 반열린 구간이다. 0·0.25·0.9·1·2·4.999·5·6초 패킷 중 앞 5초에는 6개/462바이트, 앞 1초에는 3개/186바이트가 들어온다. 경계 5초·1초 패킷은 각각 제외된다. 바이트 합은 캡처된 Ethernet 프레임 길이 합(헤더 포함, FCS 제외)이며 PCAP 파일 헤더/레코드 헤더나 HTTP 요청 수가 아니다. 5→1초 변경은 패킷이 바뀐 것이 아니라 선택 구간을 좁힌 것이다. [PCAP 형식 문서](https://www.ietf.org/ietf-ftp/internet-drafts/draft-ietf-opsawg-pcap-09.html)의 microsecond little-endian 헤더/레코드 형식을 사용한다.

### 선택 2: 문서용 IP IOC 일치·불일치

```bat
docker compose -f compose-monitor.yaml exec -T monitor-api python -m learning.educational_ioc
```

`INDICATORS = {'192.0.2.10'}`과 문자열 192.0.2.10은 일치(True), 198.51.100.20은 불일치(False)이다. [RFC 5737](https://www.rfc-editor.org/info/rfc5737/)의 문서용 주소 범위 예시이다. 지표 문자열 일치 자체가 악성 확정은 아니다. 실제 HTTP 원본에는 IP가 없어 이 예시로 실제 사용자·요청을 식별하거나 HTTP 근거를 보강할 수 없다.

### 선택 3: >= 경계와 12회 기본 사례 복구

기준 10→새 관찰 시작→위 capture_case 명령의 12를 **10으로 바꿔 실행**→1분 안에 결과 불러오기를 진행한다. 실제 목록 10회+404 한 건이면 관찰값 10·검토 후보·근거 11행이다. `http_rules.py:analyze_http`의 `len(views) >= threshold`에서 10 >= 10이 True이기 때문이다. 확인 뒤 **새 관찰 시작→capture_case 12→즉시 첫 결과**를 실행해 기본 12회·기준 10·근거 13행으로 돌아온다. 이전 DB 기록은 보존한다.

### 선택 4: AI 순수 함수 후보 코드 검토

이번 작업에서 요구 설명과 합성 예시만으로 작성한 아래 AI 초안은 **거절**했다. 실제 로그·운영 비밀값을 AI에 보내지 않았다. 모델 API 호출이나 대화 캡처는 필요 없다.

```python
# 거절한 초안: 간단하지만 과제 의미를 보존하지 못함
def candidate(rows, threshold):
    views = [r for r in rows if r['path'] == '/']
    errors = [r for r in rows if r['status_code'] == 404]
    return {'count': len(views) + len(errors),
            'matched': len(views) + len(errors) > threshold,
            'evidence': [r['id'] for r in rows]}
```

실제 코드는 `http_rules.py:select_views/find_following_errors/analyze_http`이다. 비교 결과:

| 검토 기준 | 거절 이유 / 채택한 수정 |
| --- | --- |
| 조회 조건 | 초안은 path만 확인해 POST·실패·다른 종류도 센다. 실제 코드는 GET·/·200·post_list 네 조건 모두 확인 |
| 404 문맥 | 초안은 모든 404를 횟수에 더한다. 실제 코드는 마지막 선택 조회 뒤 0 < gap <= 30인 404만 문맥 근거로 추가하고 count는 len(views) 유지 |
| 기준 경계 | 초안의 >는 실제 10회/기준 10을 놓친다. 실제 코드는 >= 유지 |
| 같은 행의 근거 | 초안은 선택하지 않은 전체 행 ID를 붙인다. 실제 코드는 선택 조회+뒤따른 오류 records에서 evidence를 구하고 조회 ID도 views에서 구함 |
| 무조회 / 순수성 | 실제 코드는 무조회 시 오류도 비우고 입력을 수정하지 않으며 DB·파일·환경·네트워크 접근을 분석 함수 밖에 둠 |

따라서 현재 순수 분석 함수를 채택했다. `tests/test_analysis.py`가 네 조건, 30초 경계, 10회 경계, 같은 근거와 무조회 등을 합성 행으로 검증한다. 합성 행은 실제 실행 결과로 주장하지 않는다.

## 3. 예상 결과와 실제 확인 상태

아래는 다른 일반 요청이 없고 전송·캡처가 성공하며 첫 결과를 시간 안에 읽었을 때의 **예상**이다. ID·시각은 DB 실값이고 예시 숫자로 고정하지 않는다.

| 상황 | 예상 관찰값 / 판정 / 근거 | 이유 |
| --- | --- | --- |
| 4회+404, 기준 10 | 원본·정규화 5행 / 조회 4 / 기준 미해당 / 근거 5 | 404는 선택 조회가 아님 |
| 12회+404, 기준 10 | 12 / 검토 후보 / 13 | 12 >= 10, 404는 문맥 1행 |
| 같은 구간 기준 20 | 12 / 기준 미해당 / 같은 13 | 같은 시각·ID, 12 >= 20은 False |
| 같은 구간 기준 10 복구 | 12 / 검토 후보 / 같은 13 | 비교 조건만 복구 |
| 새 관찰 뒤 무요청 | 0 / 기준 미해당 / 0 | 이전 행은 시작 ID 이하 |
| 실제 10회+404, 기준 10 | 10 / 검토 후보 / 11 | >= 경계 포함 |

2026-10-14 (Asia/Seoul)에 직접 확인한 결과이다. 합성 행의 테스트와 실제 요청 실행을 구분한다.

| 직접 확인 항목 | 실제 상태 |
| --- | --- |
| 순수 규칙·PCAP·IOC 테스트 | 10개 통과 |
| 호스트 Next production build | 성공 |
| Docker 빌드·Compose | 일반/API/web 세 이미지 빌드 성공, 두 config 통과, 기존 named volume 사용 |
| 기존 계정·기록 | 기존 operator 로그인 성공. 관찰 실습 전 기록 9행(#1~9)을 보존 |
| 실제 4회 및 lesson2~5 | 원본·정규화 5행(#10~14), 조회 4, 기준 10/20 False, 근거 5 |
| 실제 10회 경계·12회 복구 | 화면에서 10/기준10/후보/11행(#15~25), 새 관찰 후 12/기준10/후보/13행(#26~38) |
| 같은 실제 자료 10→20→10 | 시작 ID 25, 기준시각 2026-10-14T05:30:42.916954+00:00와 http-26~38 전체 근거 행 동일. 12/후보→12/미해당→12/후보 |
| 새 관찰 뒤 무요청 | 시작 ID 38 이후, 화면 관찰값 0·기준 미해당·근거 0, 과거 DB 행 보존 |
| 교육용 PCAP·IOC 실행 | 5초 6개/462바이트, 1초 3개/186바이트 및 문서 IP True/False 확인 |
| 기존 기능+새 분석 회귀 | 임시 DB 스키마 일반 13개·감시 27개·Sentry 보호 2개, 총 42개 통과. 실제 계정·게시글·메모·기록을 초기화하지 않음 |
| 클라우드 배포 / Classroom 채점 | 이번 작업에서 실행하지 않음 |

제출 ZIP에는 일반·감시 소스, Dockerfile·Compose·gateway, Python 의존성·npm 잠금 파일, 기존 SQL, 이 README와 DAY3_CHECKLIST를 포함한다. 실제 .env·개인 비밀값·실행 로그·DB 데이터·observation.json·PCAP·스크린샷·node_modules·.next·가상환경·캐시는 제외한다. 새 검사 스크립트나 실행 증거는 필수 제출물이 아니다. ZIP과 함께 [GitHub 저장소](https://github.com/RockCandy444/mini-watch-cloud)의 기본 브랜치 main에도 이번 완성본을 반영한다. GitHub 형식으로 제출할 때는 이 저장소 주소를 사용한다.
