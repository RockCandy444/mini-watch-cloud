"""Docker lifecycle evidence; uses only the Python standard library.
Run from repository root: python verification/run.py initial|recreate|network|rebuild|final|postmerge
"""
import argparse
import http.cookiejar
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
EVIDENCE = ROOT / 'evidence'
EVIDENCE.mkdir(exist_ok=True)
MODE = argparse.ArgumentParser()
MODE.add_argument('phase', choices=['initial', 'recreate', 'network', 'rebuild', 'final', 'postmerge'])
PHASE = MODE.parse_args().phase
LOG = EVIDENCE / f'{PHASE}.txt'
LOG.write_text('', encoding='utf-8')
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def log(text):
    print(text, flush=True)
    with LOG.open('a', encoding='utf-8', newline='\n') as f:
        f.write(text + '\n')


def run(*args, expected=0):
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    log('$ ' + ' '.join(args) + '\n' + p.stdout + p.stderr + f'[exit {p.returncode}]')
    assert p.returncode == expected, args
    return p.stdout.strip()


def compose(project, *args, expected=0):
    return run('docker', 'compose', '-f', f'compose-{project}.yaml', *args, expected=expected)


def http(port, path, data=None, expected=200):
    req = urllib.request.Request(f'http://localhost:{port}{path}',
        data=json.dumps(data).encode() if data is not None else None,
        headers={'Content-Type': 'application/json'})
    try:
        with opener.open(req, timeout=10) as response:
            code, raw = response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        code, raw = error.code, error.read().decode()
    try:
        body = json.loads(raw)
    except ValueError:
        body = {'html_received': len(raw), 'contains_board': '게시글' in raw}
    log(f'HTTP {port}{path}: {code}\n' + json.dumps(body, ensure_ascii=False))
    assert code == expected, (path, code, expected)
    return body


def wait_monitor():
    for _ in range(60):
        try:
            http(8082, '/api/auth/login', {'username': 'operator', 'password': 'Learn123!'})
            http(8082, '/api/auth/me')
            return
        except (OSError, AssertionError):
            time.sleep(1)
    raise RuntimeError('Monitor did not become ready')


def login_pair():
    http(8081, '/auth/login', {'username': 'student', 'password': 'wrong-password'}, expected=401)
    success = http(8081, '/auth/login', {'username': 'student', 'password': 'Learn123!'})
    http(8081, '/')
    return success


def events():
    return http(8082, '/api/events')['events']


def notes():
    return [http(8082, f"/api/notes/{n['id']}")['note'] for n in http(8082, '/api/notes')['notes']]


def state():
    for project in ['monitor', 'general']:
        compose(project, 'config', '--quiet')
        compose(project, 'ps')
        compose(project, 'logs', '--tail=35', f'{project}-api')
    run('docker', 'network', 'inspect', 'm5d1-events')
    compose('general', 'exec', '-T', 'general-api', 'getent', 'hosts', 'monitor-api')


if PHASE == 'initial':
    for project in ['monitor', 'general']:
        compose(project, 'config', '--quiet')
    names = run('docker', 'network', 'ls', '--format', '{{.Name}}').splitlines()
    if 'm5d1-events' not in names:
        run('docker', 'network', 'create', 'm5d1-events')
    compose('monitor', 'up', '-d', '--build')
    compose('monitor', 'exec', '-T', 'monitor-api', 'python', 'create_user.py', '--classroom')
    wait_monitor()
    compose('general', 'up', '-d', '--build')
    compose('general', 'exec', '-T', 'general-api', 'python', 'create_user.py', '--classroom')
    login_pair()
    rows = events()
    assert {('login_failure', 401), ('login_success', 200)} <= {(r['event_type'], r['status_code']) for r in rows}
    state()

elif PHASE == 'recreate':
    wait_monitor()
    before = {'events': events(), 'notes': notes()}
    assert any(n['title'] == 'Docker 점검' and n['body'] == '로그인 실패와 성공을 확인했다' for n in before['notes'])
    (EVIDENCE / 'before-recreate.json').write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding='utf-8')
    before_ids = {p: compose(p, 'ps', '-q') for p in ['general', 'monitor']}
    compose('general', 'down')
    compose('monitor', 'down')
    compose('monitor', 'up', '-d')
    wait_monitor()
    compose('general', 'up', '-d')
    after = {'events': events(), 'notes': notes()}
    assert before == after
    for p, ids in before_ids.items():
        assert ids != compose(p, 'ps', '-q')
    log('PASS: both Compose containers recreated without -v; exact event and note data preserved.')
    login_pair()
    state()

elif PHASE == 'network':
    wait_monitor()
    compose('general', 'exec', '-T', 'general-api', 'getent', 'hosts', 'general-db')
    compose('general', 'exec', '-T', 'general-api', 'getent', 'hosts', 'monitor-db', expected=2)
    before = events()
    cid = compose('general', 'ps', '-q', 'general-api')
    run('docker', 'network', 'disconnect', 'm5d1-events', cid)
    try:
        compose('general', 'exec', '-T', 'general-api', 'getent', 'hosts', 'monitor-api', expected=2)
        login_pair()
        assert before == events()
        compose('general', 'logs', '--tail=30', 'general-api')
        log('PASS: disconnected API cannot resolve monitor-api; successful local login remains unforwarded.')
    finally:
        compose('general', 'up', '-d', '--force-recreate', 'general-api')
        compose('general', 'up', '-d', '--force-recreate', 'general-gateway')
    compose('general', 'exec', '-T', 'general-api', 'getent', 'hosts', 'monitor-api')
    login_pair()
    restored = events()
    assert len(restored) == len(before) + 3
    log('PASS: Compose recreated original networks; NEW failure/success records delivered; failed sends not replayed.')

elif PHASE == 'rebuild':
    wait_monitor()
    old = http(8081, '/auth/login', {'username': 'student', 'password': 'Learn123!'})['message']
    file = ROOT / 'general/routes/auth.py'
    original = file.read_text(encoding='utf-8')
    assert '"message": "로그인 성공",' in original
    file.write_text(original.replace('"message": "로그인 성공",', '"message": "로그인 성공 · Docker 실행",'), encoding='utf-8')
    old_image = compose('general', 'images', '-q', 'general-api')
    old_container = compose('general', 'ps', '-q', 'general-api')
    compose('general', 'restart', 'general-api')
    time.sleep(2)
    assert http(8081, '/auth/login', {'username': 'student', 'password': 'Learn123!'})['message'] == old
    assert old_image == compose('general', 'images', '-q', 'general-api')
    assert old_container == compose('general', 'ps', '-q', 'general-api')
    compose('general', 'up', '-d', '--build', 'general-api')
    compose('general', 'up', '-d', '--force-recreate', 'general-gateway')
    time.sleep(2)
    assert http(8081, '/auth/login', {'username': 'student', 'password': 'Learn123!'})['message'] == '로그인 성공 · Docker 실행'
    assert old_image != compose('general', 'images', '-q', 'general-api')
    assert old_container != compose('general', 'ps', '-q', 'general-api')
    log('PASS: restart reused image/container; rebuild copied changed source into NEW image/container.')

elif PHASE == 'final':
    wait_monitor()
    login_pair()
    assert any(n['title'] == 'Docker 점검' for n in http(8082, '/api/notes')['notes'])
    compose('monitor', 'exec', '-T', 'monitor-api', 'python', '-m', 'unittest', 'discover', '-s', 'tests', '-v')
    compose('general', 'exec', '-T', 'general-api', 'python', '-m', 'unittest', 'discover', '-s', 'tests', '-v')
    state()

elif PHASE == 'postmerge':
    run('git', 'rev-parse', 'HEAD')
    compose('monitor', 'up', '-d')
    wait_monitor()
    compose('general', 'up', '-d', '--build')
    compose('general', 'up', '-d', '--force-recreate', 'general-gateway')
    before = events()
    login_pair()
    new_rows = [r for r in events() if r['id'] not in {p['id'] for p in before}]
    assert {('login_failure', 401), ('login_success', 200)} <= {(r['event_type'], r['status_code']) for r in new_rows}
    assert any(n['title'] == 'Docker 점검' and n['body'] == '로그인 실패와 성공을 확인했다' for n in notes())
    compose('monitor', 'exec', '-T', 'monitor-api', 'python', '-c',
            "import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:5000/health'); print(r.status, r.read().decode())")
    state()
    log('PASS: merged main rebuilt; new login failure/success forwarded; original note and API DB readiness confirmed.')

log('PHASE PASSED: ' + PHASE)
