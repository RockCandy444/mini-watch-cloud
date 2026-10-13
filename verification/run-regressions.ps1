# Docker-only regression runner. Credentials are local disposable fixtures.
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Push-Location $taskRoot
try {
    $mount = "type=bind,source=$taskRoot,target=/workspace,readonly"
    docker run --rm --network m5d2-general_general-data --mount $mount -w /workspace/general `
        -e DB_HOST=general-db -e DB_PORT=5432 -e DB_NAME=general_db -e DB_USER=general `
        -e DB_PASSWORD=classroom-general-only -e DB_SSLMODE=disable `
        -e SECRET_KEY=classroom-integration-secret-at-least-32-characters `
        -e EVENT_TOKEN=test-only-event-token m5d2-general-general-api python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'General regression tests failed.' }
    docker run --rm --network m5d2-monitor_monitor-data --mount $mount -w /workspace `
        -e DB_HOST=monitor-db -e DB_PORT=5432 -e DB_NAME=monitor_db -e DB_USER=monitor `
        -e DB_PASSWORD=classroom-monitor-only -e DB_SSLMODE=disable `
        -e SECRET_KEY=classroom-integration-secret-at-least-32-characters `
        m5d2-monitor-monitor-api python -m unittest discover -s monitor/backend/tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Monitor regression tests failed.' }
    Get-Content verification/test_sentry.py -Raw | docker run --rm -i `
        -e SECRET_KEY=classroom-sentry-test-secret-at-least-32-characters `
        m5d2-general-general-api python -
    if ($LASTEXITCODE -ne 0) { throw 'Sentry contract tests failed.' }
} finally {
    Pop-Location
}
