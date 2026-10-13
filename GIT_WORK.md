# Day2 Git 변경 기록

저장소 https://github.com/RockCandy444/mini-watch-cloud, 작업·배포 브랜치 day2-deploy.
최종 파일은 main에도 동일하게 반영하여 GitHub 기본 브랜치로 제출할 수 있게 한다.
원래 mini-watch-compose 저장소는 수정하지 않았다. 기존 파일·이력의 별도 사본에서 이어 작업했다.

| SHA | 변경 |
| --- | --- |
| 2e4b61d | Day1 기존 Compose·게시글·감시 기능 완료 상태. 시작 기준 |
| 6d14279f1dc1135f9ccc3755328924159fd19e54 | 세 앱 Dockerfile의 앱별 context와 PORT 실행, DB_SSLMODE, 일반 세션, 두 서버 이벤트 토큰, 감시 users 보존 이행, CSRF, 두 Sentry 초기화, Next Route Handler와 production 서버 실행 적용. 일반 실습 오류 재현 상태 포함 |
| 979f7da856ff96183e86f0c012f2c3a73ce5bf41 | general/app.py의 sentry_test() 분모 0을 1로 수정. flag와 로그인 검사 유지. verification/test_sentry.py로 404·401·500→200 및 정보 제외 확인 |
| 3ad433c228111a06f6718617e85311d340f3800d | DB 실행 환경 우선순위 수정, users·CSRF·토큰·health 회귀 테스트 갱신, HTTP smoke·스크린샷·배포 계획·필수 20/선택 4 대응·검증 실행 도구와 실제 결과 포함 |

마지막 문서 커밋은 위 실제 최종 구현·검증 SHA를 기록한다. 문서 자체의 커밋 SHA는 Git 이력에서 확인한다.

오류 수정 [diff](verification/sentry-fix.diff):

```powershell
git diff 6d14279f1dc1135f9ccc3755328924159fd19e54 979f7da856ff96183e86f0c012f2c3a73ce5bf41 -- general/app.py
git log --oneline --decorate -8
```

실제 원인은 result=1/0의 ZeroDivisionError다. result=1/1로 정상 JSON을 반환하며 다른 기존 기능을 제거하지 않았다.
ENABLE_SENTRY_TEST=false가 최종 예시이고 로그인 없는 접근 401·비활성 404를 보존한다.
재현 이미지의 오류 로그와 최종 이미지의 정상 응답을 직접 확인했다. 실제 Sentry 수신은 미확인이다.

수정 후 add·commit·push, Render의 배포 SHA 확인, 같은 로그인/요청의 정상 결과 재확인, ENABLE_SENTRY_TEST=false 복구 순서로 배포한다.
Render 배포는 아직 수행하지 않았다. Sentry Resolve만으로 코드나 배포가 바뀌지 않는다.
