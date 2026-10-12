# Docker 적용 Git 기록과 PR 검토

모든 과제 소스와 실행 증거를 본인 공개 저장소의 `main`에 push했습니다.
강의실 제출은 사용자가 직접 진행합니다.

| 커밋 | 직접 작업한 변경 |
| --- | --- |
| `95bf25128cfe80248da14a4cc8b0575c07c52ba9` | 기존 앱을 이어 사용해 두 Compose, Flask·Next.js Dockerfile, 빌드 제외 설정, 초기 SQL·볼륨, Nginx, 계정 준비 옵션, 실제 실행·화면·데이터 보존 증거 추가 |
| `113a708` | 일반 로그인 응답 문구 변경과 restart/rebuild 비교, 공유 망 분리·복구·DB 망 분리 실험, README와 실제 결과 추가 |
| `80f008a888a02d7aa54ed0897425a0f0f2b47a42` | 작업 브랜치에서 감시 API의 SELECT 1 준비 확인·Compose healthcheck·화면/gateway 대기, 정상·DB 실패 테스트와 실제 실행 증거 추가 |
| `c52c8f827122ae96346da9beb74780da9805c457` | PR 실행 로그의 줄바꿈 정리 |
| `f2db3394f9cae376cb547773288da7fb86c3556e` | PR #1의 merge commit으로 개선을 main에 병합 |

원래 앱의 시작 커밋은 `next-notes-collaboration`의 `10eb5572eaa5469b36920acfb2f49832019848c2`입니다.
새 저장소는 그 저장소 안의 mini-watch 소스만 추려 시작했고, Docker 설정·실행 실험을 별도 Git 기록으로 남겼습니다.

## 선택 4: 실제 Docker 개선 PR

- 작업 브랜치: `codex/monitor-readiness`
- PR: **https://github.com/RockCandy444/mini-watch-compose/pull/1**
- 검토 의견: https://github.com/RockCandy444/mini-watch-compose/pull/1#issuecomment-6119394352
- 병합 방식: merge commit. 실제 `MERGED` 상태·변경 파일·커밋·검토 의견은 [pr-result.json](evidence/pr-result.json)에 저장했습니다.
- GitHub에서 받은 최종 PR diff 원문: [pr-diff.txt](evidence/pr-diff.txt).

개선 전에는 DB 준비만 기다리고 API 자체의 준비를 확인하지 않았습니다.
개선 후 감시 `/health`는 실제 DB 쿼리 `SELECT 1`이 성공해야 200을 반환하고, DB 실패는 상세 정보를 노출하지 않는 503이 됩니다.
Compose의 monitor-api healthcheck가 이 응답을 검사하고 monitor-web·monitor-gateway가 API의 `service_healthy`를 기다립니다.

직접 변경한 소스는 `compose-monitor.yaml`, `monitor/backend/app.py`, `monitor/backend/tests/test_health.py`입니다.
공개 포트와 망 참여는 늘리지 않았고, 같은 Compose의 서비스만 의존하게 구성했는지 diff에서 확인했습니다.
기록·메모 조회 인증은 그대로 보호되는지 기존 통합 테스트로 확인했습니다.
본인 PR의 diff를 직접 읽고 검토 의견을 기록한 뒤 병합했습니다. 다른 사람이 독립적으로 승인한 리뷰로 주장하지 않습니다.

사용한 실제 명령:

```powershell
git switch -c codex/monitor-readiness
# healthcheck·준비 응답·테스트 변경 후 Docker 실행 검증
git add compose-monitor.yaml monitor/backend/app.py monitor/backend/tests/test_health.py evidence/final.txt
git commit -m "fix: wait for monitor API database readiness before starting gateway"
git push -u origin codex/monitor-readiness
gh pr create --repo RockCandy444/mini-watch-compose --base main --head codex/monitor-readiness --title "감시 API의 DB 준비 확인 후 화면과 gateway 시작" --body-file .local/pr-body.md
gh pr diff 1 --repo RockCandy444/mini-watch-compose --color never --allow-escape-sequences
gh pr comment 1 --repo RockCandy444/mini-watch-compose --body-file .local/pr-review.md
gh pr merge 1 --repo RockCandy444/mini-watch-compose --merge
git switch main
git pull --ff-only origin main
git log --oneline -6
```

`.local`의 PR 본문·검토 의견 임시 파일은 Git에서 제외했습니다. 실제 게시된 내용은 PR과 `pr-result.json`에서 확인할 수 있습니다.
로그 안의 터미널 색상 제어 문자 때문에 `gh pr diff`가 요구한 `--allow-escape-sequences`를 사용하여 원본 diff를 저장했습니다.

## 개선 검증과 병합 후 확인

[final.txt](evidence/final.txt)에서 감시 테스트 **14개**(기존 PostgreSQL 8개, 회원가입 프록시 4개, 준비 응답 2개)와 일반 PostgreSQL 테스트 **12개**, 총 **26개 통과**를 확인할 수 있습니다.
감시 API·두 DB는 healthy이고 7개 서비스가 실행 중입니다.

병합된 main의 커밋 식별자를 먼저 기록하고 다음을 실행했습니다.

```powershell
python verification/run.py postmerge
```

[postmerge.txt](evidence/postmerge.txt)에 일반 이미지 최종 소스 재빌드, Compose 설정 검사·ps·logs·공유 망 inspect·이름 조회,
새 로그인 실패/성공의 전달, 원래 메모 #1 상세 재조회, 내부 `/health` 200·database ready 응답을 기록합니다.
최종 문서·체크리스트 커밋은 `git log -1`과 GitHub main에서 확인할 수 있습니다.
