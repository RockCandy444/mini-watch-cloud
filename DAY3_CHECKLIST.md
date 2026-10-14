# 과제 55: 필수 20개·선택 4개 대응

2026-10-14 (Asia/Seoul). 아래는 제출 코드·문서의 자체 점검이다. Classroom 제출·채점 통과를 뜻하지 않는다. 실행 방법과 예상값/실제 확인 상태는 README의 세 부분을 기준으로 한다.

| 필수 | 충족 근거 |
| --- | --- |
| 1. 기존 소스·설정·의존성·SQL·README | general/, monitor/, common/, Dockerfile 3개, compose-general/monitor.yaml, gateway/, requirements, package-lock, 기존 SQL 보존. README 변경 파일 표 |
| 2. 응답 후 기록과 출력/전송 차이 | general/app.py:create_app → request_logging.register_request_logging → app.after_request(record_request). README 경로 1~2 |
| 3. 수신·분류·저장과 ID/수신시각 | routes/events.py:receive → event_rules.make_event → repositories/events.create_event, SQL의 IDENTITY/NOW(). README 경로 3~4 |
| 4. 서버 설정과 비밀값 보호 | Compose MONITOR_URL/EVENT_TOKEN/GENERAL_API_URL, X-Event-Token 검증. Next는 서버 MONITOR_API_URL만 참조. 실제 .env 제외, README 설정 표 |
| 5. 실제 요청 캡처 | learning/capture_case.py:capture_case의 urllib 요청, 사전 MAX(id)와 이후 DB SELECT, HTTP 상태/DB 행 일치 검증. 고정 JSON/INSERT 없음 |
| 6. 원본 복사 정규화 | normalize_event의 dict(original), http-ID/http_live/kind, 방법·경로·상태·같은 수신 순간 보존. IP/계정 생성 없음 |
| 7. 같은 파일 실습 경로 | support.DATA_PATH/read_observation → lesson2~5. README의 PC 임시 JSON 성공 시 교체 절차 |
| 8. 네 조건 행 선택 | http_rules.select_views: GET·/·200·post_list 모두 적용, 목록 반환 |
| 9. 같은 조회 목록의 횟수/ID | analyze_http에서 len(views), view_ids; 404는 count에서 제외 |
| 10. >= 판정과 4/12/20 설명 | analyze_http의 len(views) >= threshold. README 예상 결과 표, lesson4 같은 파일의 10/20 비교 |
| 11. 마지막 조회 뒤 404 | find_following_errors가 마지막 선택 조회 시각과 전체 정규화 행 비교, 0 < gap <= 30 |
| 12. 문맥만 추가·무조회 처리 | views 없으면 오류 []; records=views+errors, count=len(views) |
| 13. 새 관찰 ID 경계·과거 보존 | support.current_boundary/analysis.observation의 SELECT MAX(id). DELETE/초기화 없음. 실제 기존 #1~9 보존 확인 |
| 14. ID와 최근 60초 조건 | read_recent의 id > after_id 및 reference-60 <= occurred_at <= reference. DB 기준시각을 재사용. README 경로 8 |
| 15. 로그인·검증·실제 DB 전달 | analysis.py 두 API require_login, threshold/after_id/reference_time 형식·범위·중복 검증. read_recent 결과를 build_report에 전달 |
| 16. HTTP 카드 한 개와 12/13 차이 | report.build_report cards 한 개, observed/threshold/verdict/reason/evidence/records 계산. 실제 12회/13행 확인 |
| 17. 화면 조작·근거 표 | src/components/AnalysisClient.js, Dashboard, 서버 프록시. ID·UTC 수신시각·방법·경로·상태·종류 표시 |
| 18. 같은 구간의 기준 비교·상태 초기화 | AnalysisClient의 observation.after_id/reference_time 재사용, begin의 report/observation 초기화. 실제 기준 10→20→10에서 같은 경계/시각/전체 행 확인 |
| 19. 실행·예상·확인 상태 구분 | README 세 부분, 최초 API rebuild와 이후 restart 조건, web rebuild/gateway restart, 1분 내 첫 조회, 실패 재시도 |
| 20. 해석 한계와 교육 자료 분리 | report.limitation, README 범위 설명. report는 HTTP 원본만 입력, educational_pcap/ioc와 분리 |

| 선택 | 충족 근거 |
| --- | --- |
| 1. PCAP 생성·읽기·시간 선택·패킷/바이트 | educational_pcap.py의 generate/read_packets/summarize. 직접 생성 자료. 실행 확인: 5초 6개/462바이트, 1초 3개/186바이트. README 선택 1 |
| 2. 문서 IP IOC 일치/불일치 | educational_ioc.py의 match_ioc. 직접 확인 True/False, 실제 HTTP에 IP가 없어 적용하지 않음. README 선택 2 |
| 3. 실제 10회 경계·12회 복구 | capture_case 10 + 화면 기준 10 실제 확인: 10·검토 후보·11행 (#15~25). 이어 새 관찰+12회로 12·검토 후보·13행 (#26~38) 복구. README 선택 3의 >= 설명 |
| 4. AI 후보 구체 검토 | README 선택 4의 거절 초안 및 네 조건·404 시간 문맥·>=·같은 행 근거 대조 표. 현재 순수 함수 채택 이유, 실제 로그/비밀값 전송 없음 |

## 직접 실행한 범위

- 호스트 Next production build와 세 Docker 이미지 빌드 성공, 두 Compose config 통과.
- 임시 DB 스키마 회귀: 일반 13개·감시 27개(새 순수 10개와 API 통합 3개 포함)·기존 Sentry 보호 2개, 총 42개 통과.
- 실제 4회 캡처: 원본/정규화 5행, 조회 4행, 기준 10/20 모두 False.
- 실제 10회·12회·기준 변경·새 관찰 0회: 기존 계정으로 브라우저 화면에서 확인.
- 화면 근거 http-26~http-38과 DB 원본 #26~38 대조, 기존 기록 #1~9 보존 확인.
- PCAP·IOC 모듈을 각각 직접 실행, 현재 코드와 README 수치 일치.
- 클라우드 배포 및 Classroom 최종 제출/채점은 이번 작업에서 하지 않았다.
